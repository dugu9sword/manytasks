import itertools
import re
from typing import List, Tuple
from collections import defaultdict

import jstyleson

from manytasks.defs import Arg, Task, TaskPool


def check_key(ele):
    if isinstance(ele, str) and ele.startswith("-"):
        try:
            float(ele.lstrip("-"))
            return False
        except:
            return True
    else:
        return False


def nonekey_generator():
    idx = 0
    while True:
        idx += 1
        yield "__{}".format(idx)


def parse_config(config: dict) -> List[Tuple[str, List]]:
    nonekey = nonekey_generator()
    ret = []
    
    current_key = None
    for ele in config:
        if check_key(ele):
            if current_key is not None:
                ret.append((current_key, ["✔"]))
            current_key = ele
        else:
            # convert int/float to str, and pass it to the next `if` statement
            if isinstance(ele, int) or isinstance(ele, float):
                ele = str(ele)
            # key-value or non-key value?
            if isinstance(ele, list):
                values = ele
            if isinstance(ele, str) and ele != "":
                values = parse_string(ele) 
            if current_key:
                ret.append((current_key, values))
                current_key = None  
            else:
                ret.append((next(nonekey), values))
    if current_key is not None:
        ret.append((current_key, ["✔"]))
    return ret


def config_to_tasks(executor, configs):
    ret = []
    # [(k1, [v1, v2]), (k2, [v1])] -> [[(k1, v1), (k1, v2])], [(k2, v1)]]
    expand_configs = []
    for conf in configs:
        expand_configs.append([(conf[0], ele) for ele in conf[1]])
    for arg_list in itertools.product(*expand_configs):
        args = []
        for arg in arg_list:
            args.append(Arg(key=arg[0], value=str(arg[1])))
        ret.append(Task(executor, args))
    return ret


def parse_string(string):
    """
        Test Case:

            print(parse_string("$<1:6:2;2>"))
            print(parse_string("$<1:4>"))
            print(parse_string("$<a|b|c>"))
            print(parse_string("$<a|b|c>.$<1:4>"))
            print(parse_string("$<[f'{i:03}' for i in range(1, 10, 2)]>"))
            print(parse_string("$<os.listdir()>"))
    """
    enum_lists = []
    enum_idx = 0
    # Step 1. analyze the string to find all possible cases to enumerate
    while True:
        found = re.search(r"\$\<[^>]*\>", string)
        if not found:
            break
        
        enum_repr = found.group()

        while "SWITCH":
            # Case I
            #   $<start:end:[step]:[zfill]>
            found = re.search(r"^(-?\d+)(:-?\d+)(:-?\d+)?(;\d+)?$", enum_repr[2:-1])
            if found:
                start = int(found.group(1))
                end = int(found.group(2)[1:])
                step = int(found.group(3)[1:]) if found.group(3) else None
                zero_num = int(found.group(4)[1:]) if found.group(4) else None
                if step:
                    r = range(start, end, step)
                else:
                    r = range(start, end)
                if zero_num:
                    enum_list = list(str(i).zfill(zero_num) for i in r)
                else:
                    enum_list = list(str(i) for i in r)
                break

            # Case II
            #   $<a|b|c|d>
            found = re.search(r"^([^|]+\|)+[^|]+$", enum_repr[2:-1])
            if found:
                enum_list = enum_repr[2:-1].split("|")
                break

            # Case Fallback
            #   $<python-script>
            try:
                enum_list = list(eval(enum_repr[2:-1]))
            except Exception:
                print("Error occurs when parsing {}: {}!".format(string, enum_repr))
                exit(1)

            break

        string = string.replace(enum_repr, f'🔢<{enum_idx}>')
        enum_lists.append(enum_list)
        enum_idx += 1
        
    # Step 2. expand the string to list
    if enum_idx == 0:
        ret = [string]
    else:
        enum_product = list(itertools.product(*enum_lists))
        ret = []
        for i in range(len(enum_product)):
            tmp = string
            for eid in range(enum_idx):
                tmp = tmp.replace(f'🔢<{eid}>', str(enum_product[i][eid]))
            ret.append(tmp)   
        
    return ret


def apply_arg_reference(tasks: List[Task]):
    for task in tasks:
        for arg in task:
            key, val = arg.key, arg.value
            while True:
                found = re.search(r"\$\{[^}]+\}", val)
                if not found:
                    break
                arg_ref = found.group()

                while "SWITCH":
                    # Case I: ${--key[start_idx:end_idx]}
                    found = re.search(r"^([^\[]+)\[(\d*):(-?\d*)\]$", arg_ref[2:-1])
                    if found:
                        refered_key = found.group(1)
                        start_idx = int(found.group(2)) if found.group(2) else 0
                        end_idx = int(found.group(3)) if found.group(3) else None
                        new_val = task[refered_key][start_idx:end_idx]
                        break
                    
                    # Case II: ${--key[pattern1:val1,pattern2:val2,_:default]}
                    found = re.search(r"^([^\[]+)\[((([^:]+):([^,]+))+)\]$", arg_ref[2:-1])
                    if found:
                        refered_key, pairs = found.group(1), found.group(2)
                        refered_val = task[refered_key]
                        pairs = dict(re.findall(r"([^:]+):([^,]+),?", pairs))
                        if "_" in pairs:
                            pairs = defaultdict(lambda: pairs["_"], pairs)
                        new_val = pairs[refered_val]
                        break
                    
                    # arg_ref ~ key
                    new_val = task[arg_ref[2:-1]]
                    break
                val = val.replace(arg_ref, new_val)
            task[key] = val


def load_taskpool(path):
    config = jstyleson.load(fp=open(path))
    executor = config["executor"].split(" ")
    base_conf = parse_config(config["configs"]["==base=="])
    more_confs = list(map(parse_config, config["configs"]["==more=="]))
    if len(more_confs) == 0:
        more_confs = [[]]
    tasks = []
    for more_conf in more_confs:
        tasks.extend(config_to_tasks(executor, base_conf + more_conf))
    apply_arg_reference(tasks)
    taskpool = TaskPool()
    taskpool.set_tasks(tasks)
    return taskpool
