# log.py
#
# Implemented functions for debugging and logging
# Written by Juhyun Song

# flag (todo: make selectable)
SHOW_PAYLOAD = True

# prefix
KAFL_PREFIX = '\033[1;34m[KAFL]\033[0m '
PYTHON_PREFIX = '\033[1;32m[PYTHON]\033[0m '
YELLOW_PREFIX = '\033[1;33m[DEBUG]\033[0m '

def debug(msg):
    print(PYTHON_PREFIX + msg)

def debug_kafl(msg):
    print(KAFL_PREFIX + msg)

def debug_log(msg):
    print(YELLOW_PREFIX + msg)