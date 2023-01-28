import os
import time

import jstyleson
import yaml
from tabulate import tabulate

from manytasks.defs import Reserved, TaskPool


def log(*info, target='cf'):
    assert target in ['c', 'f', 'cf', 'fc']
    info_str = str("\n".join(info))
    if 'c' in target:
        print(info_str)
    if 'f' in target:
        logger = globals()["__logger__"]
        logger.write("{}\n".format(info_str))
        logger.flush()


def log_config(filename, log_path, append=False):
    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)
    logger = open("{}/{}.txt".format(log_path, filename),
                  "a" if append else "w")
    globals()["__logger__"] = logger


def current_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def human_readable_time_delta(x):
    x = int(x)
    h = x // (60 * 60)
    x = x % (60 * 60)
    m = x // 60
    s = x % 60
    return f"{h:02}:{m:02}:{s:02}"


def draw_logo():
    log("""
    =================================================================
                                      _____              _         
          /\/\    __ _  _ __   _   _ /__   \  __ _  ___ | | __ ___ 
         /    \  / _` || '_ \ | | | |  / /\/ / _` |/ __|| |/ // __| 
        / /\/\ \| (_| || | | || |_| | / /   | (_| |\__ \|   < \__ \ 
        \/    \/ \__,_||_| |_| \__, | \/     \__,_||___/|_|\_\|___/ 
                               |___/                               
    =================================================================
    """)


def show_task_list(taskpool: TaskPool, target="cf"):
    log(">>>>>> Show the task list...", target=target)
    header = ['idx'] + taskpool.keys
    table = [header]
    for idx, task in enumerate(taskpool):
        values = []
        for key in taskpool.keys:
            if key in task.keys:
                if Reserved.is_reserved(task[key]):
                    values.append(Reserved.symbol(task[key]))
                else:
                    values.append(task[key])
            else:
                values.append("-")
        table.append([idx] + values)
    log(tabulate(table), target=target)
    log(target=target)


def read_from_console(prompt, default):
    ret = input("{} (default: {}) :".format(prompt, default)).strip()
    if ret == "":
        ret = default
    return ret


def safe_append(a, b):
    if not a.endswith(b):
        return a + b
    else:
        return a


def safe_cut(a, b):
    if a.endswith(b):
        return a[:-len(b)]
    else:
        return a


def exists_fast_fail(p):
    if not os.path.exists(p):
        print("{} not exists!".format(p))
        exit()


def init_config():
    path = read_from_console("Input the config name", "config")
    jstyleson.dump(
        {
            "executor": "python main.py",
            "cuda": [],
            "concurrency": 1,
            "cuda_per_task": 1,
            "configs": {
                "==base==": [],
                "==more==": []
            }
        },
        open("{}.json".format(path), "w"),
        indent=4)


def init_rule():
    path = read_from_console("Input the rule name", "rule")
    yaml.dump(
        {
            "accuracy": {
                "filter": {
                    "include": "words must be included",
                },
                "pattern": "accuracy <FLOAT>",
                "reduce": "max"
            },
            "loss": {
                "filter": {
                    "exclude": "words must be excluded"
                },
                "pattern": "loss <FLOAT>",
                "reduce": "min"
            }
        },
        open("{}.yaml".format(path), "w"),
        indent=4)
