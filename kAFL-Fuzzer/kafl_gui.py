#!/usr/bin/env python3.8
#
# Copyright (C) 2017-2019 Sergej Schumilo, Cornelius Aschermann, Tim Blazytko
# Copyright (C) 2019-2020 Intel Corporation
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Given a kAFL workdir, produce a text-based UI with status summary/overview.
"""

import curses
import string
import msgpack
import os
import sys
import time
import inotify.adapters
import glob
import psutil
from common.util import read_binary_file
from threading import Thread, Lock

class Interface:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.y = 0

    def print_banner(self):
        # self.stdscr.addstr(self.y, 0, "{0:^80}".format("kAFL", "(testKafl)"), curses.color_pair(3))
        # self.stdscr.addstr(self.y, 0, "{0:^80}".format("(testKafl)"), curses.color_pair(2))
        # self.y += 1
        # self.stdscr.addstr(self.y, 0, "{0:^80}".format("2020 KITRI BEST OF THE BEST"), curses.color_pair(5))
        # self.y += 1
        # self.y += 1
        SVCNAME = "Smells like Teen spirit"
        title1 = 'kAFL '
        title2 = f'({SVCNAME})'
        title3 = '2020 KITRI Best of the Best'

        center_len = len(title1) + len(title2)
        pad_len1 = (80 - center_len) // 2
        pad_len2 = (80 - len(title3)) // 2
        pad1 = ' ' * pad_len1
        pad2 = ' ' * pad_len2
        
        x = 0

        self.stdscr.addstr(self.y, x, pad1)
        x += pad_len1
        self.stdscr.addstr(self.y, x, title1, curses.color_pair(3) + curses.A_BOLD)
        x += len(title1)
        self.stdscr.addstr(self.y, x, title2, curses.color_pair(2) + curses.A_BOLD)
        x += len(title2)
        self.stdscr.addstr(self.y, x, pad1)
        self.y += 1

        x = 0
        self.stdscr.addstr(self.y, x, pad2)
        x += pad_len2
        self.stdscr.addstr(self.y, x, title3, curses.color_pair(5) + curses.A_BOLD)
        self.y += 2
    
    def print_first_line(self):
        self.stdscr.addstr(self.y, 0, '┌─', curses.A_DIM)
        self.stdscr.addstr(self.y, 2, ' guest timing ', curses.color_pair(5))
        self.stdscr.addstr(self.y, 16, '─'*37 + '┬─', curses.A_DIM)
        self.stdscr.addstr(self.y, 55, ' overall results ', curses.color_pair(5))
        self.stdscr.addstr(self.y, 72, '─'*7 + '┐', curses.A_DIM)
        self.y += 1

    def print_sixth_line(self):
        self.stdscr.addstr(self.y, 0, '├─', curses.A_DIM)
        self.stdscr.addstr(self.y, 2, ' execution progress ', curses.color_pair(5))
        self.stdscr.addstr(self.y, 22, '─'*14 + '┬─', curses.A_DIM)
        self.stdscr.addstr(self.y, 38, ' map coverage ', curses.color_pair(5))
        self.stdscr.addstr(self.y, 52,  '─┴'+ '─'*25 + '┤', curses.A_DIM)
        self.y += 1

    def print_ninth_line(self):
        self.stdscr.addstr(self.y, 0, '├─', curses.A_DIM)
        self.stdscr.addstr(self.y, 2, ' node progress ', curses.color_pair(5))
        self.stdscr.addstr(self.y, 17, '─'*19 + '┼─', curses.A_DIM)
        self.stdscr.addstr(self.y, 38, ' machine stats ', curses.color_pair(5))
        self.stdscr.addstr(self.y, 53, '─'*26 + '┤', curses.A_DIM)
        self.y += 1

    def print_twelfth_line(self):
        self.stdscr.addstr(self.y, 0, '├─', curses.A_DIM)
        self.stdscr.addstr(self.y, 2, ' payload info ', curses.color_pair(5))
        self.stdscr.addstr(self.y, 16, '─'*20 + '┴─', curses.A_DIM)
        self.stdscr.addstr(self.y, 37, '─'*42 + '┤', curses.A_DIM)
        self.y += 1

    def print_sixteenth_line(self):
        self.stdscr.addstr(self.y, 0, '└' + '─'*78 + '┘', curses.A_DIM)

    def print_title_line(self, title):
        title = "[%s%s]" % (title, " " * (len(title) % 2))
        pad = '░' * ((80 - len(title)) // 2)
        self.stdscr.addstr(self.y, 0, pad + title + pad)
        self.y += 1

    def print_sep_line(self):
        self.stdscr.addstr(self.y, 0, '━' * 80)
        self.y += 1

    def print_thin_line(self):
        self.stdscr.addstr(self.y, 0, '├' + '─' * 78 + '┤')
        self.y += 1

    def print_empty(self):
        self.stdscr.addstr(self.y, 0, '┃' + ' ' * 78 + '┃')
        self.y += 1

    def print_info_line(self, pairs, sep=" │ ", end="│", prefix=""):
        x = 0
        infos = []
        for info in pairs:
            infolen = len(info[1]) + len(info[2])
            if infolen == 0:
                infos.append(" ".ljust(info[0]+2))
            else:
                infos.append(" %s : %s %s" % (
                    info[1], info[2], " ".ljust(info[0]-infolen)))

        # self.stdscr.addstr(self.y, 0, '│' + prefix + sep.join(infos) + " " + end)
        self.stdscr.addstr(self.y, x, '│', curses.A_DIM)
        x += 1
        for info in infos:
            self.stdscr.addstr(self.y, x, prefix + info + " ")
            x += len(info)
            self.stdscr.addstr(self.y, x, sep, curses.A_DIM)
            x += len(sep)
            self.stdscr.addstr(self.y, x, " ", curses.A_DIM)
            x += len(" ")
        
        # self.stdscr.addstr(self.y, x, end, curses.A_DIM)
        self.y += 1

    def refresh(self):
        self.y = 0
        self.stdscr.refresh()

    def clear(self):
        self.stdscr.clear()

    def print_hexdump(self, data, max_rows=10):
        width = 16
        for ri in range(0, max_rows):
            row = data[width * ri:width * (ri + 1)]
            if len(row) > 0:
                self.print_hexrow(row, offset=ri * width)
            else:
                self.print_empty()

    def print_hexrow(self, row, offset=0):
        def map_printable(char):
            s_char = chr(char)
            if s_char in string.printable and s_char not in "\t\n\r\x0b\x0c":
                return s_char
            return "."

        def map_hex(char):
            return hex(char)[2:].ljust(2, "0")

        prefix = "┃0x%07x: " % offset
        hex_dmp = prefix + (" ".join(map(map_hex, row)))
        hex_dmp = hex_dmp.ljust(61)
        print_dmp = ("".join(map(map_printable, row)))
        print_dmp = print_dmp.ljust(16)
        print_dmp = "│" + print_dmp + " ┃"
        self.stdscr.addstr(self.y, 0, hex_dmp)
        self.stdscr.addstr(self.y, len(hex_dmp), print_dmp)
        self.y += 1


def pnum(num):
    assert num >= 0
    if num <= 9999:
        return "%d" % num
    num /= 1000.0
    if num <= 999:
        return "%.1fk" % num
    num /= 1000.0
    if num <= 999:
        return "%.1fm" % num
    num /= 1000.0
    if num <= 999:
        return "%.1fg" % num
    num /= 1000.0
    if num <= 999:
        return "%.1ft" % num
    num /= 1000.0
    if num <= 999:
        return "%.1fp" % num
    assert False

def pbyte(num):
    assert num >= 0
    if num <= 999:
        return "%d" % num
    num /= 1024.0
    if num <= 999:
        return "%.1fk" % num
    num /= 1024.0
    if num <= 999:
        return "%.1fm" % num
    num /= 1024.0
    if num <= 999:
        return "%.1fg" % num
    num /= 1024.0
    if num <= 999:
        return "%.1ft" % num
    num /= 1024.0
    if num <= 999:
        return "%.1fp" % num
    assert False


def pfloat(flt):
    assert flt >= 0
    if flt <= 999:
        return "%.1f" % flt
    return pnum(flt)


def ptime(secs):
    if not secs:
        return "none seen yet"
    if secs < 2: # clear the jitter
        return "Just Now!"
    secs = int(secs)
    seconds = secs % 60
    secs //= 60
    mins = secs % 60
    secs //= 60
    hours = secs % 24
    days = secs  // 24
    
    return "%d days, %d hrs, %d min, %d sec" % (days, hours, mins, seconds)

def ptime_sec(secs):
    if not secs:
        return ""
    if secs < 2:
        return "Just Now!"

class GuiDrawer:
    def __init__(self, workdir, stdscr):
        self.gui_mutex = Lock()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)
        default_col = curses.color_pair(1)

        # Fenster und Hintergrundfarben
        stdscr.bkgd(default_col)
        self.gui = Interface(stdscr)
        self.stdscr = stdscr
        self.current_slave_id = 0

        self.finished = False
        self.data = GuiData(workdir)
        self.watcher = Thread(target=self.watch, args=(workdir,))
        self.cpu_watcher = Thread(target=self.watch_cpu, args=())
        self.loop = Thread(target=self.loop, args=())
        self.watcher.daemon = True
        self.watcher.start()
        self.cpu_watcher.daemon = True
        self.cpu_watcher.start()

        stdscr.refresh()
        self.loop.start()
        self.loop.join()

    def draw(self):
        d = self.data
        self.gui.print_banner()
        self.gui.print_first_line()
        self.gui.print_info_line([
            (46, "     run time", ptime(d.runtime())),
            (17, "  crash", "%s" % (pnum((d.num_found("crash")))))])
                                                 #ptime_sec(d.time_since("crash"))))])
        self.gui.print_info_line([
            (46, "last new path", ptime(d.time_since("regular"))),
            (17, " addsan", "%s" % (pnum((d.num_found("kasan")))))])
                                                 #ptime_sec(d.time_since("kasan"))))]) 
        self.gui.print_info_line([
            (46, "   last crash", ptime(d.time_since("crash"))),
            (17, "timeout", "%s" % (pnum((d.num_found("timeout")))))])
                                                 #ptime_sec(d.time_since("timeout"))))])
        self.gui.print_info_line([
            (46, " last timeout", ptime(d.time_since("timeout"))),
            (17, "regular", "%s" % (pnum((d.num_found("regular")))))])
                                                 #ptime_sec(d.time_since("regular"))))])

        self.gui.print_sixth_line()
        self.gui.print_info_line([
            (29, "  total execs", pnum(d.total_execs())),
            (34, "      edges", "%s" % (pnum((d.bitmap_used()))))])
        self.gui.print_info_line([
            (29, "   exec speed", str(pnum(d.execs_p_sec_avg())) + "/sec"),
            (34, "map density", "%s" % pfloat(d.p_coll()) + "%")])

        self.gui.print_ninth_line()
        for i in range(0, d.num_slaves()):
            hl = " "
            if i == self.current_slave_id:
                hl = ">"
            nid = d.slave_input_id(i)
            if nid not in [None, 0]:
                self.gui.print_info_line([
                    (29, "      node id", str(d.slave_input_id(i))),
                    (34, "   cpu used", pnum(d.cpu_used()) + "%")])
                self.gui.print_info_line([
                    (29, "   now trying", d.slave_stage(i)),
                    (34, "memory used", pnum(d.ram_used()) + "%")])
            else:
                self.gui.print_info_line([
                    (29, "      node id", "N/A"),
                    (34, "   cpu used", pnum(d.cpu_used()) + "%")])
                self.gui.print_info_line([
                    (29, "   now trying", d.slave_stage(i)),
                    (34, "memory used", pnum(d.ram_used()) + "%")])
        
        self.gui.print_twelfth_line()
        self.gui.print_info_line([
            (72, "    parent id", "%d" % d.node_parent_id(nid))])
        self.gui.print_info_line([
            (72, "         size", pbyte(d.node_size(nid)) + " bytes")])
        self.gui.print_info_line([
            (72, "      payload", pbyte(d.node_size(nid)))])

        self.gui.print_sixteenth_line()

        self.gui.refresh()

    def loop(self):
        d = self.data
        while True:
            char = self.stdscr.getch()
            self.gui_mutex.acquire()
            theme = 0
            try:
                if char == curses.KEY_UP:
                    self.current_slave_id = (self.current_slave_id - 1) % d.num_slaves()
                elif char == curses.KEY_DOWN:
                    self.current_slave_id = (self.current_slave_id + 1) % d.num_slaves()
                elif char == ord("q") or char == ord("Q"):
                    self.finished = True
                    return
                self.draw()
            finally:
                self.gui_mutex.release()
                time.sleep(0.01)

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
            self.gui_mutex.acquire()
            try:
                (_, type_names, path, filename) = event
                d.update(path, filename)
                self.draw()
            finally:
                self.gui_mutex.release()

    def watch_cpu(self):
        while True:
            if self.finished:
                return
            cpu_info = psutil.cpu_times_percent(interval=2, percpu=False)
            mem_info = psutil.virtual_memory()
            swap_info = psutil.swap_memory()
            self.gui_mutex.acquire()
            try:
                self.data.mem = mem_info
                self.data.cpu = cpu_info
                self.data.swap = swap_info
                self.draw()
            finally:
                self.gui_mutex.release()


class GuiData:

    def __init__(self, workdir):
        self.workdir = workdir
        self.execs_avg = 0
        self.slave_stats = list()
        self.load_initial()

    def load_initial(self):
        print("Waiting for slaves to launch..")
        self.cpu = psutil.cpu_times_percent(interval=0.01, percpu=False)
        self.mem = psutil.virtual_memory()
        self.cores_phys = psutil.cpu_count(logical=False)
        self.cores_virt = psutil.cpu_count(logical=True)
        self.stats = self.read_file("stats")

        num_slaves = self.stats.get("num_slaves",0)
        for slave_id in range(0, num_slaves):
            self.slave_stats.append(self.read_file("slave_stats_%d" % slave_id))

        # TODO frontend is using time.time() when we actually need time.clock(), plus perhaps the startup time/date
        self.starttime = min([x["start_time"] for x in self.slave_stats])

        self.nodes = {}
        for metadata in glob.glob(self.workdir + "/metadata/node_*"):
            self.load_node(metadata)
        self.aggregate()

    def load_node(self, name):
        node_id = int(name.split("_")[-1])
        self.nodes[node_id] = self.read_file("metadata/node_%05d" % node_id)

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


    def target(self):
        return "foo"

    def config(self):
        return "bar"

    def runtime(self):
        return max([x["run_time"] for x in self.slave_stats])

    def execs_p_sec(self):
        return sum([x["execs/sec"] for x in self.slave_stats])

    def execs_p_sec_avg(self):
        return self.total_execs()/self.runtime()

    def slave_execs_p_sec(self, sid):
        return self.slave_stats[i].get(["execs/sec"],0)

    def total_execs(self):
        return sum([x["total_execs"] for x in self.slave_stats])

    def num_slaves(self):
        return len(self.slave_stats)

    def num_found(self, reason):
        return self.aggregated["exit_reasons"][reason]

    def time_since(self, reason):
        time_stamp = self.aggregated["last_found"][reason]
        if not time_stamp:
            return None
        return self.starttime + self.runtime() - time_stamp

    def pending_fav(self):
        if self.fav_total() > 0:
            return 100 * (self.fav_total() - self.fav_fin()) / float(self.fav_total())
        return 0

    def stability(self):
        # chance p() to survive 100 executions: ((total-crashes)/total)^100
        if self.total_execs() == 0:
            return 0
        n = self.total_execs()
        c = self.total_reloads()
        return 100*((n-c)/n)**100

    def total_reloads(self):
        total_reloads = 0
        for slave_info in self.slave_stats:
            total_reloads += slave_info["num_reload"]
        return total_reloads

    def reload_p_sec(self):
        return self.total_reloads()/self.runtime()

    def cycles(self):
        return self.stats.get("cycles", 0)

    def cpu_total(self):
        return "%d(%d)" % (self.cores_phys, self.cores_virt)

    def cpu_cores(self):
        return self.cores_phys

    def cpu_used(self):
        return self.cpu.user + self.cpu.system

    def cpu_user(self):
        return self.cpu.user - self.cpu.guest

    def cpu_vm(self):
        return self.cpu.guest

    def ram_total(self):
        return self.mem.total

    def ram_avail(self):
        return self.mem.available

    def ram_used(self):
        return 100 * float(self.mem.used) / float(self.mem.total)

    def swap_used(self):
        return self.swap.used

    def yield_imported(self):
        return self.stats["yield"].get("import", 0)

    def yield_init(self):
        return (self.stats["yield"].get("trim", 0) +
                self.stats["yield"].get("trim_funky", 0) +
                self.stats["yield"].get("calibrate", 0))

    def yield_grim(self):
        return (self.stats["yield"].get("grim_inference", 0) +
                self.stats["yield"].get("grim_generalize", 0) +
                self.stats["yield"].get("grim_recursive", 0) +
                self.stats["yield"].get("grim_extension", 0) +
                self.stats["yield"].get("grim_repl_str", 0))

    def yield_redq(self):
        return (self.stats["yield"].get("redq_mutate", 0) +
                self.stats["yield"].get("redq_dict", 0))

    def yield_color(self):
        return self.stats["yield"].get("redq_coloring", 0)

    def yield_havoc(self):
        return (self.stats["yield"].get("afl_havoc", 0) +
                self.stats["yield"].get("afl_splice", 0))

    def yield_det(self):
        return (self.stats["yield"].get("afl_arith_1", 0) +
                self.stats["yield"].get("afl_arith_2", 0) +
                self.stats["yield"].get("afl_arith_4", 0) +
                self.stats["yield"].get("afl_flip_1/1", 0) +
                self.stats["yield"].get("afl_flip_2/1", 0) +
                self.stats["yield"].get("afl_flip_4/1", 0) +
                self.stats["yield"].get("afl_flip_8/1", 0) +
                self.stats["yield"].get("afl_flip_8/2", 0) +
                self.stats["yield"].get("afl_flip_8/4", 0) +
                self.stats["yield"].get("afl_int_1", 0) +
                self.stats["yield"].get("afl_int_2", 0) +
                self.stats["yield"].get("afl_int_4", 0))


    def normal_total(self):
        return (self.normal_init() + self.normal_redq() + self.normal_deter() +
                self.normal_havoc() + self.normal_fin())

    def normal_init(self):
        return self.aggregated["normal_states"].get("initial", 0)

    def normal_redq(self):
        return self.aggregated["normal_states"].get("redq/grim", 0)

    def normal_deter(self):
        return self.aggregated["normal_states"].get("deterministic", 0)

    def normal_havoc(self):
        return self.aggregated["normal_states"].get("havoc", 0)
        return 0

    def normal_fin(self):
        return self.aggregated["normal_states"].get("final", 0)

    def fav_total(self):
        return (self.fav_init() + self.fav_redq() +
                self.fav_deter() + self.fav_havoc() + self.fav_fin())

    def fav_init(self):
        return self.aggregated["fav_states"].get("initial", 0)

    def fav_redq(self):
        return self.aggregated["fav_states"].get("redq/grim", 0)

    def fav_deter(self):
        return self.aggregated["fav_states"].get("deterministic", 0)

    def fav_havoc(self):
        return self.aggregated["fav_states"].get("havoc", 0)

    def fav_fin(self):
        return self.aggregated["fav_states"].get("final", 0)

    def bitmap_size(self):
        return 64 * 1024

    def bitmap_used(self):
        return self.stats["bytes_in_bitmap"]

    def paths_total(self):
        return self.stats["paths_total"]

    def p_coll(self):
        return 100.0 * float(self.bitmap_used()) / float(self.bitmap_size())

    def slave_stage(self, i):
        method = self.slave_stats[i].get("method", None)
        stage  = self.slave_stats[i].get("stage", "[waiting..]")
        if method:
            #return "%s/%s" % (stage[0:6],method[0:12])
            return "%s" % method[0:14]
        else:
            return stage[0:14]

    def slave_execs_p_sec(self, i):
        return self.slave_stats[i].get("execs/sec")

    def slave_total_execs(self, i):
        return self.slave_stats[i].get("total_execs")

    def slave_input_id(self, i):
        return self.slave_stats[i]["node_id"]

    def node_size(self, nid):
        return self.nodes[nid]["payload_len"]

    def node_level(self, nid):
        return self.nodes[nid].get("level", 0)

    def node_parent_id(self, nid):
        return self.nodes[nid]["info"]["parent"]

    def node_fav_bits(self, nid):
        if not self.nodes.get(nid, None):
            return -1
        favs = self.nodes[nid].get("fav_bits", None)
        if favs:
            return len(favs)
        else:
            return 0

    def node_new_bytes(self, nid):
        return len(self.nodes[nid]["new_bytes"])

    def node_new_bits(self, nid):
        return len(self.nodes[nid]["new_bits"])

    def node_exit_reason(self, nid):
        return self.nodes[nid]["info"]["exit_reason"][0]

    def node_payload(self, nid):
        exit_reason = self.nodes[nid]["info"]["exit_reason"]
        filename = self.workdir + "/corpus/%s/payload_%05d" % (exit_reason, nid)
        return read_binary_file(filename)[0:1024]  # TODO remove path traversal vuln
    
    def load_slave(self, id):
        self.slave_stats[id] = self.read_file("slave_stats_%d" % id)

    def load_global(self):
        self.stats = self.read_file("stats")

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


def main(stdscr, workdir):
    
    GuiDrawer(workdir, stdscr)

    import locale
    locale.setlocale(locale.LC_ALL, '')
    code = locale.getpreferredencoding()

    curses.wrapper(main)

# if len(sys.argv) == 2:
#     curses.wrapper(main)
# else:
#     print("Usage: " + sys.argv[0] + " <kafl-workdir>")