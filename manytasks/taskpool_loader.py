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
            # key-value or non-key value?
            if isinstance(ele, list):
                if current_key:
                    ret.append((current_key, ele))
                    current_key = None
                else:
                    ret.append((next(nonekey), ele))
                continue
            # convert int/float to str, and pass it to the next `if` statement
            if isinstance(ele, int) or isinstance(ele, float):
                ele = str(ele)
            if isinstance(ele, str) and ele != "":
                if ele[0] == '{' and ele[-1] == '}':
                    try:
                        val = list(eval(ele[1:-1]))
                        if current_key:
                            ret.append((current_key, val))
                            current_key = None
                        else:
                            ret.append((next(nonekey), val))
                    except Exception:
                        print("Error occurs when parsing {}: {}!".format(current_key, ele))
                        exit(1)
                    continue
                if current_key:
                    ret.append((current_key, [ele]))
                    current_key = None  
                else:
                    ret.append((next(nonekey), [ele]))
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


def apply_arg_reference(tasks: List[Task]):
    for task in tasks:
        for arg in task:
            key, val = arg.key, arg.value
            if val[0] == "<" and val[-1] == ">":
                val = val[1:-1]
                while True:
                    found = re.search(r"\[[^]]*\]", val)
                    if not found:
                        break
                    arg_ref = found.group()

                    if re.search(r"([^:]*):([-]*\d*):([-]*\d*):(\d*)", arg_ref[1:-1]):
                        # arg_ref ~ [key:start_idx:end_idx:length]
                        refered_key, start_idx, end_idx, length = arg_ref[1:-1].split(":")
                        start_idx = int(start_idx) if start_idx != "" else 0
                        end_idx = int(end_idx) if end_idx != "" else 0
                        length = int(length) if length != "" else 0
                        assert not (end_idx != 0 and length != 0)
                        if end_idx != 0:
                            new_val = task[refered_key][start_idx:end_idx]
                        if length != 0:
                            new_val = task[refered_key][start_idx:start_idx+length]
                    elif re.search(r"([^:]):([^;@]+@[^;]+)", arg_ref[1:-1]):
                        # arg_ref ~ [key:pattern@val;pattern@val;pattern@val;_@default]
                        refered_key, pairs = arg_ref[1:-1].split(":")
                        refered_val = task[refered_key]
                        pairs = dict(re.findall(r"([^@;]+)@([^;]+)[;]?", pairs))
                        if "_" in pairs:
                            pairs = defaultdict(lambda: pairs["_"], pairs)
                        new_val = pairs[refered_val]
                    else:
                        # arg_ref ~ [key]
                        new_val = task[arg_ref[1:-1]]
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
