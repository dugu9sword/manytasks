import multiprocessing
from typing import List, Tuple

import jstyleson
import psutil

from manytasks import shared
from manytasks.shared import Arg, Task


def next_config_idx(configs, config_idx):
    idx = -1
    ret = list(config_idx)
    while True:
        if idx < -len(config_idx):
            return None
        ret[idx] += 1
        if ret[idx] < len(configs[idx][1]):
            return ret
        else:
            ret[idx] = 0
            idx -= 1


def gen_tasks(configs):
    tmp_configs = []
    for i in range(len(configs)):
        if not isinstance(configs[i][1], list):
            tmp_configs.append((configs[i][0], [configs[i][1]]))
        else:
            tmp_configs.append((configs[i][0], configs[i][1]))
    configs = tmp_configs

    task_list: List[Task] = []
    config_idx = [0 for _ in range(len(configs))]
    while config_idx is not None:
        task: Task = []
        for i in range(len(configs)):
            task.append(Arg(key=configs[i][0], value=str(configs[i][1][config_idx[i]])))
        task_list.append(task)
        config_idx = next_config_idx(configs, config_idx)
    if len(set(map(tuple, task_list))) < len(task_list):
        print("Seems that some tasks shares the same args")
        exit()
    return task_list


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
                    ret.append((current_key, ele))
                    current_key = None  
                else:
                    ret.append((next(nonekey), ele))
    return ret


def load_config(path="sample_config.json"):
    config = jstyleson.load(fp=open(path))

    shared.executor = config["executor"]
    
    cuda = config["cuda"]
    if cuda == [] or cuda == -1:
        cuda = [-1]
    
    if cuda[0] != -1 and psutil.WINDOWS:
        print("CUDA shoule be -1 on windows")
        exit()
    shared.cuda = cuda
    

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
    shared.concurrency = concurrency
    
    base_conf = parse_config(config["configs"]["==base=="])
    more_confs = list(map(parse_config, config["configs"]["==more=="]))
    tasks = []
    if len(more_confs) == 0:
        tasks.extend(gen_tasks(base_conf))
    else:
        for more_conf in more_confs:
            tasks.extend(gen_tasks(base_conf + more_conf))
    shared.tasks = tasks


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
