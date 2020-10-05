#!/usr/bin/python3
"""
Automatically generate user-land agent binary
with a interface recovery result file. (JSON)
"""
import sys
import json
import argparse

NUM_CODE = 0        # number of control codes

SVCNAME = None      # driver service name (inside output or manually given)

ITERS = 1 << 16     # number of fuzz tests per control code

LOCATOR = '/* INITIALIZE ioctl_code HERE */'

# initialize argument parser
parser = argparse.ArgumentParser(description='Generate Windows user-land agent with a interface recovery output')
parser.add_argument('filename', help='interface recovery output file (JSON)', type=str)
parser.add_argument('-name', help='driver service name (not required if already in output file)', required=False, type=str)
args = parser.parse_args()

SVCNAME = args.name

# load output data (JSON)
try:
    json_f = open(args.filename, 'r')
except:
    print('Could not open output file.')
    sys.exit(1)
json_data = json.load(json_f)   # JSON data
json_f.close()

if_arr = []     # list of ioctl control codes

# read service name from output file
if SVCNAME is None:
    try:
        SVCNAME = json_data['svcname']
    except KeyError:
        print('No service name is given!')
        print('Use -name option if service name is not present on output file')
        sys.exit(1)

# add control codes to the list
if_dict = json_data['interfaces']
for el in if_dict:
    if_arr.append(int(el['code'], 16))

NUM_CODE = len(if_arr)

# open user-land agent source code
f = open('./templates/template.c', 'r')
data = f.read()
f.close()

# patch the code with the recovery output
data = data.replace('__NUM_CODE__', str(NUM_CODE))
data = data.replace('__SVCNAME__', SVCNAME)
data = data.replace('__ITERS__', str(ITERS))
idx = data.find(LOCATOR)
front = data[:idx + len(LOCATOR) + 1]
back = data[idx + len(LOCATOR) + 1:]

stub = ''
for i in range(len(if_arr)):
    stub = stub + '\tioctl_code[{}] = {};\n'.format(i, if_arr[i])
data = front + stub + back

# write the new agent code
f = open('./templates/agent.c', 'w')
f.write(data)
f.close()
