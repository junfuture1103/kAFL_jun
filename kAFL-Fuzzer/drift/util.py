import json
from drift.interface import Interface

def get_interfaces(iff):
    """Parse JSON file given with -iff option
    and instantiate interfaces to get a full list
    
    Arguments:
        iff -- JSON result file"""
    json_f = open(iff, 'r')
    json_data = json.load(json_f)   # json data
    json_f.close()

    if_arr = []     # list of interfaces

    if_dict = json_data['interfaces']
    for el in if_dict:
        code = int(el['code'], 16)
        if_arr.append(Interface(code))  # instantiate and add to list

    return if_arr