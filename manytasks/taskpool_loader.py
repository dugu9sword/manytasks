import itertools
import re
import os
import glob
from typing import List, Tuple
from collections import defaultdict

import jstyleson

from manytasks.defs import Arg, Reserved, Task, TaskPool


def is_key(ele):
    if isinstance(ele, str) and ele.startswith("-"):
        try:
            float(ele.lstrip("-"))
            return False
        except:
            return True
    else:
        return False


def nonekey_generator(prefix=None):
    idx = 0
    while True:
        idx += 1
        if prefix is None:
            yield "__{}".format(idx)
        else:
            yield "__{}.{}".format(prefix, idx)


def parse_config(cfg_name, config: list) -> List[Tuple[str, List]]:
    """
        Input:  parse_config(None, [
                    "data",
                    "--multigpu",
                    "--fp16", "$<?>",
                    "--a", [1, 2],
                    "-b", "$<1:4>"
                ])
        Return: [
                    ("__1", ["data"]),
                    ("--multigpu", ["$_ON_"]),
                    ("--fp16", ["$_ON_", "$_OFF_"]),
                    ("--a", ["1", "2"]),
                    ("-b", ["1", "2", "3"])
                ]
    """
    nonekey = nonekey_generator(cfg_name)
    ret = []
    
    pending_key = None
    for ele in config:
        if is_key(ele):
            if pending_key is not None:
                ret.append((pending_key, [Reserved.ON]))
            pending_key = ele
        else:
            # convert int/float to str, and pass it to the next `if` statement
            if isinstance(ele, int) or isinstance(ele, float):
                ele = str(ele)
            # key-value or non-key value?
            if isinstance(ele, list):
                values = ele
            if isinstance(ele, str):
                values = parse_string(ele)
            if pending_key:
                ret.append((pending_key, values))
                pending_key = None
            else:
                ret.append((next(nonekey), values))
    if pending_key is not None:
        ret.append((pending_key, [Reserved.ON]))
    return ret


def parse_string(string):
    """
        Test Case:

            print(parse_string("$<1:6:2;2>"))
            print(parse_string("$<1:4>"))
            print(parse_string("$<a|b|c>"))
            print(parse_string("$<a|b|c>.$<1:4>"))
            print(parse_string("$<?>"))
    """
    enum_lists = []
    enum_idx = 0
    # Step 1. analyze the string to find all possible cases to enumerate
    while True:
        found = re.search(r"\$\<[^>]*\>", string)
        if not found:
            break
        
        enum_repr = found.group()
        enum_start, enum_end = found.start(), found.end()

        while "SWITCH":
            # Case I
            #   $<?>
            if enum_repr.strip() == "$<?>":
                enum_list = [Reserved.ON, Reserved.OFF]
                break

            # Case II
            #   $<start:end:[step];[zfill]>
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

            # Case III
            #   $<a|b|c|d>
            found = re.search(r"^([^|]+\|)+[^|]+$", enum_repr[2:-1])
            if found:
                enum_list = enum_repr[2:-1].split("|")
                break

            # Case IV
            #   $<files:manytasks/*.py>
            found = re.search(r"^files:([^;]*)(;nameonly)?$", enum_repr[2:-1])
            if found:
                enum_list = glob.glob(found.group(1))
                if found.group(2) is not None:
                    enum_list = [os.path.basename(ele) for ele in enum_list]
                break

            # Case V
            #   $<lines:lines.txt>
            found = re.search(r"^lines:(.*)$", enum_repr[2:-1])
            if found:
                enum_list = open(found.group(1)).readlines()
                enum_list = [ele.strip() for ele in enum_list]
                enum_list = [ele for ele in enum_list if ele != ""]
                break

        string = string[:enum_start] + f"#ENUM<{enum_idx}>" + string[enum_end:]
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
                tmp = tmp.replace(f'#ENUM<{eid}>', str(enum_product[i][eid]))
            ret.append(tmp)

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


def apply_arg_reference(tasks: List[Task]):
    for task in tasks:
        for arg in task:
            key, val = arg.key, arg.value
            # print("processing", key, val)
            while True:
                found = re.search(r"\$\{[^}]+\}", val)
                if not found:
                    break
                arg_ref = found.group()

                while "SWITCH":
                    # Case I: ${key[start_idx:end_idx]}
                    found = re.search(r"^([^\[]+)\[(\d*):(-?\d*)\]$", arg_ref[2:-1])
                    if found:
                        refered_key = found.group(1)
                        refered_key = task.smart_key(refered_key)
                        start_idx = int(found.group(2)) if found.group(2) else 0
                        end_idx = int(found.group(3)) if found.group(3) else None
                        new_val = task[refered_key][start_idx:end_idx]
                        break
                    
                    # Case II: ${key[pattern1:val1,pattern2:val2,_:default]}
                    found = re.search(r"^([^\[]+)\[((([^:]+):([^,]+))+)\]$", arg_ref[2:-1])
                    if found:
                        refered_key, pairs = found.group(1), found.group(2)
                        refered_key = task.smart_key(refered_key)
                        refered_val = task[refered_key]
                        pairs = dict(re.findall(r"([^:]+):([^,]+),?", pairs))
                        if "_" in pairs:
                            pairs = defaultdict(lambda: pairs["_"], pairs)
                        new_val = pairs[refered_val]
                        break
                    
                    # Case III: ${key}
                    refered_key = arg_ref[2:-1]
                    refered_key = task.smart_key(refered_key)
                    new_val = task[refered_key]
                    break
                val = val.replace(arg_ref, new_val)
            task[key] = val


def load_taskpool(path):
    config = jstyleson.load(fp=open(path))
    executor = config["executor"].split(" ")
    base_conf = parse_config(None, config["configs"]["==base=="])
    more_confs = []
    for mid, more_conf in enumerate(config["configs"]["==more=="]):
        more_confs.append(parse_config(mid, more_conf))
    if len(more_confs) == 0:
        more_confs = [[]]
    tasks = []
    for more_conf in more_confs:
        tasks.extend(config_to_tasks(executor, base_conf + more_conf))
    apply_arg_reference(tasks)
    taskpool = TaskPool()
    taskpool.set_tasks(tasks)
    return taskpool
