import time
import glob
import random
import psutil
import curses
import msgpack
import inotify.adapters
from threading import Thread, Lock
from common.util import read_binary_file

from kafl_fuzz import PAYQ, LOGQ

WORKDIR = ''
SVCNAME = ''

# screen width
WIDTH = 80

# color pair code
WHITE = 1
RED = 2
GREEN = 3
YELLOW = 4
BLUE = 5
MAGENTA = 6
CYAN = 7

# box drawing characters
B_HR = '─'
B_VT = '│'
B_LU = '┌'
B_LM = '├'
B_LD = '└'
B_CU = '┬'
B_CM = '┼'
B_CD = '┴'
B_RU = '┐'
B_RM = '┤'
B_RD = '┘'


# helper function for color pairs
def color(code):
    return curses.color_pair(code)


# helper function for formatting timestamps
def ptime(secs):
    if not secs:
        return "None Yet"

    secs = int(secs)
    seconds = secs % 60
    secs //= 60
    mins = secs % 60
    secs //= 60
    hours = secs % 24
    days = secs  // 24
    return "%2d days,%2d hrs,%2d min,%2d sec" % (days, hours, mins, seconds)


class MonitorInterface:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.y = 0

    def print_test(self):
        x = 0

        # data = PAYQ.get()
        self.stdscr.addstr(self.y, x, ' ' * 40)
        self.stdscr.addstr(self.y, x, 'aaaa') 
        self.y += 1

    def print_title(self):
        title1 = 'kAFL '
        title2 = f'({SVCNAME})'
        title3 = '2020 KITRI Best of the Best'

        center_len = len(title1) + len(title2)
        pad_len1 = (WIDTH - center_len) // 2
        pad_len2 = (WIDTH - len(title3)) // 2
        pad1 = ' ' * pad_len1
        pad2 = ' ' * pad_len2
        
        x = 0
        self.y += 1     # empty line

        self.stdscr.addstr(self.y, x, pad1)
        x += pad_len1
        self.stdscr.addstr(self.y, x, title1, color(YELLOW))
        x += len(title1)
        self.stdscr.addstr(self.y, x, title2, color(GREEN))
        x += len(title2)
        self.stdscr.addstr(self.y, x, pad1)
        self.y += 1

        x = 0
        self.stdscr.addstr(self.y, x, pad2)
        x += pad_len2
        self.stdscr.addstr(self.y, x, title3, color(CYAN))
        self.y += 2

    def print_guest_and_overall(self, data):
        # line 1
        frag1 = '┌─ '
        frag2 = '───────────────────────────────────────┬─ '
        frag3 = '─────┐'
        title1 = 'guest timing '
        title2 = 'overall results '
        
        x = 0
        self.stdscr.addstr(self.y, x, frag1)
        x += len(frag1)
        self.stdscr.addstr(self.y, x, title1, color(CYAN))
        x += len(title1)
        self.stdscr.addstr(self.y, x, frag2)
        x += len(frag2)
        self.stdscr.addstr(self.y, x, title2, color(CYAN))
        x += len(title2)
        self.stdscr.addstr(self.y, x, frag3)
        self.y += 1

        # line 2
        frag1 = '│        run time :'
        runtime = ptime(data.runtime())

        x = 0
        self.stdscr.addstr(self.y, x, frag1)
        x += len(frag1)
        self.stdscr.addstr(self.y, x, runtime)
        x += len(runtime)
        
        self.y += 1


    def refresh(self):
        self.y = 0
        self.stdscr.refresh()


class MonitorData:
    def __init__(self, workdir):
        self.workdir = workdir
        self.exec_avg = 0
        self.slave_stats = []
        self.load_initial()

    def load_initial(self):
        print("Waiting for slaves to launch..")
        self.cpu = psutil.cpu_times_percent(interval=0.01, percpu=False)
        self.mem = psutil.virtual_memory()
        self.cores_phys = psutil.cpu_count(logical=False)
        self.cores_virt = psutil.cpu_count(logical=True)
        self.stats = self.read_file("stats")

        # add slave stats
        num_slaves = self.stats.get("num_slaves",0)
        for slave_id in range(0, num_slaves):
            self.slave_stats.append(self.read_file("slave_stats_%d" % slave_id))
            self.starttime = min([x["start_time"] for x in self.slave_stats])

        # add node information
        self.nodes = {}
        for metadata in glob.glob(self.workdir + "/metadata/node_*"):
            self.load_node(metadata)
        self.aggregate()

    def load_node(self, name):
        node_id = int(name.split("_")[-1])
        self.nodes[node_id] = self.read_file("metadata/node_%05d" % node_id)

    def runtime(self):
        return max([x["run_time"] for x in self.slave_stats])

    def aggregate(self):
        self.aggregated = {
            "fav_states": {},
            "normal_states": {},
            "exit_reasons": {"regular": 0, "crash": 0, "kasan": 0, "timeout": 0},
            "last_found": {"regular": 0, "crash": 0, "kasan": 0, "timeout": 0}
        }

        for nid in self.nodes:
            node = self.nodes[nid]
            self.aggregated["exit_reasons"][node["info"]["exit_reason"]] += 1
            if node["info"]["exit_reason"] == "regular":
                states = self.aggregated["normal_states"]
                if len(node["fav_bits"]) > 0:
                    states = self.aggregated["fav_states"]
                nodestate = node["state"]["name"]
                states[nodestate] = states.get(nodestate, 0) + 1

            last_found = self.aggregated["last_found"][node["info"]["exit_reason"]]
            this_found = node["info"]["time"]
            if last_found < this_found:
                self.aggregated["last_found"][node["info"]["exit_reason"]] = this_found

    def load_slave(self, id):
        self.slave_stats[id] = self.read_file("slave_stats_%d" % id)

    def load_global(self):
        self.stats = self.read_file("stats")

    def num_slaves(self):
        return len(self.slave_stats)

    def update(self, pathname, filename):
        if "node_" in filename:
            self.load_node(pathname + "/" + filename)
            self.aggregate()
        elif "slave_stats" in filename:
            for i in range(0, self.num_slaves()):
                self.load_slave(i)
        elif filename == "stats":
            self.load_global()

    def read_file(self, name):
        retry = 4
        data = None
        while retry > 0:
            try:
                data = read_binary_file(self.workdir + "/" + name)
                break
            except:
                retry -= 1
        if data:
            return msgpack.unpackb(data, raw=False, strict_map_key=False)
        else:
            return None


class MonitorDrawer:
    def __init__(self, stdscr):
        global WORKDIR

        # mutex lock
        self.inf_mutex = Lock()

        # create pairs of forground and background colors
        curses.init_pair(WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(RED, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(MAGENTA, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(CYAN, curses.COLOR_CYAN, curses.COLOR_BLACK)

        # set default color pair
        stdscr.bkgd(curses.color_pair(1))

        # create drawing interface
        self.inf = MonitorInterface(stdscr)
        self.stdscr = stdscr

        # create initial statistics
        self.finished = False
        self.data = MonitorData(WORKDIR)

        # create child threads for loop
        self.watcher = Thread(target=self.watch, args=(WORKDIR,))
        self.cpu_watcher = Thread(target=self.watch_cpu, args=())
        self.thread_loop = Thread(target=self.loop)

        # start watcher threads
        self.watcher.daemon = True
        self.watcher.start()
        self.cpu_watcher.daemon = True
        self.cpu_watcher.start()

        # start loop thread
        stdscr.refresh()
        self.thread_loop.start()
        self.thread_loop.join()
    
    def loop(self):
        while True:
            try:
                self.draw()
            finally:
                time.sleep(0.1)

    def watch(self, workdir):
        d = self.data
        mask = (inotify.constants.IN_MOVED_TO)
        self.inotify = inotify.adapters.Inotify()
        i = self.inotify
        i.add_watch(workdir, mask)
        i.add_watch(workdir + "/metadata/", mask)

        for event in i.event_gen(yield_nones=False):
            if self.finished:
                return
            self.inf_mutex.acquire()
            try:
                (_, type_names, path, filename) = event
                d.update(path, filename)
                self.draw()
            finally:
                self.inf_mutex.release()

    def watch_cpu(self):
        while True:
            if self.finished:
                return
            cpu_info = psutil.cpu_times_percent(interval=2, percpu=False)
            mem_info = psutil.virtual_memory()
            swap_info = psutil.swap_memory()
            self.inf_mutex.acquire()
            try:
                self.data.mem = mem_info
                self.data.cpu = cpu_info
                self.data.swap = swap_info
                self.draw()
            finally:
                self.inf_mutex.release()

    def draw(self):
        # statistics
        data = self.data

        self.inf.print_title()

        # payload
        self.inf.print_test()

        # self.inf.print_guest_and_overall(data)

        # fflush screen
        self.inf.refresh()


def run(stdscr):
    MonitorDrawer(stdscr)


def main(workdir):
    global WORKDIR, SVCNAME
    
    WORKDIR = workdir
    SVCNAME = 'testDriver'  # todo - receive in args

    # delay for files to be generated
    time.sleep(1)

    curses.wrapper(run)