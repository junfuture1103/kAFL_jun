# log.py
#
# Implemented functions for debugging and logging
# Written by Juhyun Song

KAFL_PREFIX = '\033[1;34m[PYTHON]\033[0m '

PYTHON_PREFIX = '\033[1;32m[PYTHON]\033[0m '

def debug(msg):
    print(PYTHON_PREFIX + msg)

def debug_kafl(msg):
    print(KAFL_PREFIX + msg)