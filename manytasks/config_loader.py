import itertools
import multiprocessing
import re
from typing import List, Tuple

import jstyleson
import psutil

from manytasks.shared import Arg, Settings, Task, TaskPool


def read_from_console(prompt, default):
    ret = input("{} (default: {}) :".format(prompt, default)).strip()
    if ret == "":
        ret = default
    return ret


def init_config():
    path = read_from_console("Input the config name", "config")
    jstyleson.dump(
        {
            "executor": "python main.py",
            "cuda": [-1],
            "concurrency": 1,
            "configs": {
                "==base==": [],
                "==more==": []
            }
        }, open("{}.json".format(path), "w"), indent=4)


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
        if current_key is None and check_key(ele):
            current_key = ele
            continue
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
    return ret


def config_to_tasks(configs):
    ret = []
    # [(k1, [v1, v2]), (k2, [v1])] -> [[(k1, v1), (k1, v2])], [(k2, v1)]]
    expand_configs = []
    for conf in configs:
        expand_configs.append([(conf[0], ele) for ele in conf[1]])
    for arg_list in itertools.product(*expand_configs):
        args = []
        for arg in arg_list:
            args.append(Arg(key=arg[0], value=str(arg[1])))
        ret.append(Task(args))
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
                    found_key = found.group()
                    val = val.replace(found_key, task[found_key[1:-1]])
                task[key] = val


def load_config(path="sample_config.json"):
    settings = Settings()
    config = jstyleson.load(fp=open(path))

    settings.executor = config["executor"]
    
    cuda = config["cuda"]
    if cuda == [] or cuda == -1:
        cuda = [-1]
    if cuda[0] != -1 and psutil.WINDOWS:
        print("CUDA shoule be -1 on windows")
        exit()
    settings.cuda = cuda
    
    concurrency = config["concurrency"]
    if concurrency == "#CUDA":
        if cuda[0] != -1:
            concurrency = len(cuda)
        else:
            print("You must specify which CUDA devices you want to use if concurrency is set to #CUDA.")
    elif concurrency == "#CPU":
        concurrency = max(1, multiprocessing.cpu_count() - 1)
    else:
        concurrency = int(concurrency)
    settings.concurrency = concurrency
    
    # generating all tasks
    base_conf = parse_config(config["configs"]["==base=="])
    more_confs = list(map(parse_config, config["configs"]["==more=="]))
    if len(more_confs) == 0:
        more_confs = [[]]
    tasks = []
    for more_conf in more_confs:
        tasks.extend(config_to_tasks(base_conf + more_conf))
    apply_arg_reference(tasks)
    TaskPool().set_tasks(tasks)
