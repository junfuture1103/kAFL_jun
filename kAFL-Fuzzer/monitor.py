#!/usr/bin/env python3.8
#
# Copyright (C) 2017-2019 Sergej Schumilo, Cornelius Aschermann, Tim Blazytko
# Copyright (C) 2019-2020 Intel Corporation
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Launcher for Fuzzing with kAFL. Check fuzzer/core.py for more.
"""

import os
import sys
import signal

import common.color
from common.self_check import self_check
from common.config import FuzzerConfiguration

# Experimental
from multiprocessing import Process, Queue, Pool
import kafl_mon

KAFL_ROOT = os.path.dirname(os.path.realpath(__file__)) + "/"
KAFL_BANNER = KAFL_ROOT + "banner.txt"
KAFL_CONFIG = KAFL_ROOT + "kafl.ini"

# Shared queue and signal between fuzzer and monitor
PAYQ = Queue()

def sigint_handler(sig, frame):
    sys.exit(0)

def main():
    if not self_check(KAFL_ROOT):
        return 1

    import fuzzer.core
    cfg = FuzzerConfiguration(KAFL_CONFIG)
    workdir = cfg.argument_values['work_dir']

    # Check terminal window size
    row, col = os.popen('stty size', 'r').read().split()
    if int(row) < 24 or int(col) < 82:
        print("Your terminal is too small to show monitor!")
        sys.exit()

    import kafl_conf
    kafl_conf.SHOW_PAYLOAD = True   # payload should be transferred through queue
    kafl_conf.ENABLE_TUI = True
    kafl_conf.ENABLE_LOG = False    # other logging scheme should be off
    
    procs = []
    procs.append(Process(target=fuzzer.core.start, args=(cfg,)))
    procs.append(Process(target=kafl_mon.main, args=(workdir,)))

    for proc in procs:
        proc.start()

    for proc in procs:
        proc.join()

    # Default behavior
    # Exetute fuzzer only and print log through terminal
    else:
        import kafl_conf
        kafl_conf.ENABLE_TUI = False
        fuzzer.core.start(cfg)
        

if __name__ == "__main__":
    main()
