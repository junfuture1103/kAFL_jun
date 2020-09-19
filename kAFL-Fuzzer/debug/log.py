# log.py
#
# Implemented functions for debugging and logging
# Written by Juhyun Song

# flag (todo: make selectable)
DEBUG_STATE = True
DEBUG_SHOW_PAYLOAD = True

# prefix
EXCEPT_PREFIX = '\033[1;31m[EXCEPT]\033[0m '
ERROR_PREFIX = '\033[1;31m[EXCEPT]\033[0m '
WARN_PREFIX = '\033[1;31m[WARNING]\033[0m '
KAFL_PREFIX = '\033[1;34m[KAFL]\033[0m '
INFO_PREFIX = '\033[1;32m[INFO]\033[0m '
YELLOW_PREFIX = '\033[1;33m[DEBUG]\033[0m '

def debug_info(msg):
    print(INFO_PREFIX + msg)

def debug_kafl(msg):
    print(KAFL_PREFIX + msg)

def debug_warn(msg):
    print(WARN_PREFIX + msg)

def debug_error(msg):
    print(ERROR_PREFIX + msg)

def debug_except(msg):
    print(EXCEPT_PREFIX + msg)

def debug(msg, newline=False):
    if newline:
        print('\n' + YELLOW_PREFIX + msg)
    else:
        print(YELLOW_PREFIX + msg)