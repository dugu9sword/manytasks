from typing import NamedTuple
from colorama import Fore, Back
from concurrent.futures import ProcessPoolExecutor
import subprocess
from multiprocessing import Manager
import time
import os
from typing import List
from threading import Thread
from argparse import ArgumentParser
import hjson
from flask import Flask, url_for, send_file
from alchemist import glob
from alchemist.glob import ArgGroupList, ArgGroup, Arg
from alchemist.webui import app, available_port, init_gpu_handles
import re
from tabulate import tabulate
from time import sleep
from pathlib import Path
import random


def log(*info, target='cf'):
    assert target in ['c', 'f', 'cf', 'fc']
    info_str = str("\n".join(info))
    if 'c' in target:
        print(info_str)
    if 'f' in target:
        logger = globals()["__logger__"]
        logger.write("{}\n".format(info_str))
        logger.flush()



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


def gen_arg_list(configs):
    tmp_configs = []
    for i in range(len(configs)):
        if not isinstance(configs[i][1], list):
            tmp_configs.append((configs[i][0], [configs[i][1]]))
        else:
            tmp_configs.append((configs[i][0], configs[i][1]))
    configs = tmp_configs

    arg_group_list: ArgGroupList = []
    config_idx = [0 for _ in range(len(configs))]
    while config_idx is not None:
        args: ArgGroup = []
        for i in range(len(configs)):
            args.append(Arg(key=configs[i][0],
                            value=configs[i][1][config_idx[i]]))
        arg_group_list.append(args)
        config_idx = next_config_idx(configs, config_idx)
    return arg_group_list


def log_config(filename, log_path, append=False):
    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)
    logger = open("{}/{}.txt".format(log_path, filename),
                  "a" if append else "w")
    globals()["__logger__"] = logger


def load_task(path="sample_task.hjson"):
    task = hjson.load(fp=open(path))
    executor = task["executor"]
    runnable = task["runnable"]
    cuda = task["cuda"]
    if cuda == [] or cuda == -1:
        cuda = [-1]
    concurrency = task["concurrency"]
    base_conf = task["configs"]["==base=="]
    more_confs = task["configs"]["==more=="]
    _base_conf = []
    for ele in base_conf:
        if isinstance(base_conf[ele], list):
            _base_conf.append((ele, base_conf[ele]))
        else:
            _base_conf.append((ele, [base_conf[ele]]))
    _more_confs = []
    for more_conf in more_confs:
        _more_conf = []
        for ele in more_conf:
            if isinstance(more_conf[ele], list):
                _more_conf.append((ele, more_conf[ele]))
            else:
                _more_conf.append((ele, [more_conf[ele]]))
        _more_confs.append(_more_conf)
    parsed_confs = []
    if len(_more_confs) == 0:
        parsed_confs.append(_base_conf)
    for _more_conf in _more_confs:
        parsed_confs.append(_base_conf + _more_conf)
    return executor, runnable, cuda, concurrency, parsed_confs


manager = Manager()
cuda_num = manager.dict()
cuda_lock = manager.Lock()


def acquire_cuda():
    with cuda_lock:
        min_cuda_idx = -1
        min_cuda_task_num = 1000
        for cuda_idx in cuda_num.keys():
            if cuda_num[cuda_idx] < min_cuda_task_num:
                min_cuda_idx = cuda_idx
                min_cuda_task_num = cuda_num[cuda_idx]
        # log("Current CUDA usage {}, select {}".format(
        #     cuda_num, min_cuda_idx))
        cuda_num[min_cuda_idx] += 1
    return min_cuda_idx


def release_cuda(cuda_idx):
    with cuda_lock:
        cuda_num[cuda_idx] -= 1


def current_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def arg2str(arg_group):
    return " ".join(list(map(lambda arg: "{}={}".format(arg.key, arg.value), arg_group)))


def run_task(executor, runnable, arg_group):
    task_idx = glob.arg_group_list.index(arg_group)
    cuda_idx = acquire_cuda()
    args_str = arg2str(arg_group)
    log("[{}] {} TASK {}/{} {} : {}".format(
        current_time(),
        "START",
        glob.arg_group_list.index(arg_group),
        len(glob.arg_group_list),
        "(ON CUDA {})".format(cuda_idx) if cuda_idx != -1 else "",
        args_str))
    with open("{}/task-{}.txt".format(glob.log_path, glob.arg_group_list.index(arg_group)), 'w') as output:
        env = os.environ.copy()
        if cuda_idx != -1:
            env["CUDA_VISIBLE_DEVICES"] = str(cuda_idx)
        callee = [executor, runnable]
        for arg in arg_group:
            callee.append("{}={}".format(arg.key, arg.value))
        glob.arg_group_status[task_idx] = "running"
        ret = subprocess.call(callee,
                              stdout=output,
                              stderr=output,
                              env=env)
        log("[{}] {} TASK {}/{} {} WITH RETURN ID {} : {}".format(
            current_time(),
            "FINISH",
            glob.arg_group_list.index(arg_group),
            len(glob.arg_group_list),
            "(ON CUDA {})".format(cuda_idx) if cuda_idx != -1 else "",
            ret,
            args_str))
        release_cuda(cuda_idx)
        return ret


def main():
    parser = ArgumentParser()
    parser.add_argument('--task', dest='task_path', action='store', default="sample_task",
                        help='Specify the task name')
    parser.add_argument('--random', dest='random_exe', action='store_true',
                        help='Specify the task name')
    parsed_args = parser.parse_args()
    task_path = parsed_args.task_path
    random_exe = parsed_args.random_exe
    if ".hjson" not in task_path:
        task_path += '.hjson'
    glob.task_name = task_path

    if not os.path.exists(task_path):
        print("Task {} not found.".format(task_path))
        exit()
    glob.log_path = "{}.logs".format(task_path[:-6])

    if os.path.exists(glob.log_path):
        override = input("Logs for task {} exists, input [y] to override: ".format(task_path))
        if override != 'y':
            print("Task canceled.")
            exit()
    for p in Path(glob.log_path).glob("task-*.txt"):
        p.unlink()

    log_config("alchemist", log_path=glob.log_path)
    glob.executor, glob.runnable, glob.cuda, glob.concurrency, parsed_confs = load_task(task_path)
    for cuda_id in glob.cuda:
        cuda_num[cuda_id] = 0

    log("""
    =================================================================
                 _          _                          _         _   
         /\     | |        | |                        (_)       | |  
        /  \    | |   ___  | |__     ___   _ __ ___    _   ___  | |_ 
       / /\ \   | |  / __| | '_ \   / _ \ | '_ ` _ \  | | / __| | __|
      / ____ \  | | | (__  | | | | |  __/ | | | | | | | | \__ \ | |_ 
     /_/    \_\ |_|  \___| |_| |_|  \___| |_| |_| |_| |_| |___/  \__|
    =================================================================
    """)

    log("Load task from {}".format(task_path),
        "- executor: {}".format(glob.executor),
        "- runnable: {}".format(glob.runnable),
        "- cuda: {}".format(str(glob.cuda)),
        "- concurrency: {}".format(glob.concurrency))

    for config in parsed_confs:
        # print(gen_arg_list(config))
        glob.arg_group_list.extend(gen_arg_list(config))
    glob.arg_group_status = ["pending"] * len(glob.arg_group_list)
    if random_exe:
        random.shuffle(glob.arg_group_list)

    log("Mappings(idx->args)")
    keys = []
    for arg_group in glob.arg_group_list:
        for ele in arg_group:
            if ele.key not in keys:
                keys.append(ele.key)
    header = ['idx'] + keys
    table = [header]
    for idx, arg_group in enumerate(glob.arg_group_list):
        # log("\t{} : {}".format(idx, arg2str(arg_group)), target='cf')
        values = []
        for key in keys:
            found = False
            for ele in arg_group:
                if ele.key == key:
                    found = True
                    values.append(ele.value)
                    break
            if not found:
                values.append("-")
        table.append([idx] + values)
    log(tabulate(table))

    # Start UI
    init_gpu_handles()
    port = available_port()
    ui_thread = Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": port})
    ui_thread.daemon = True
    ui_thread.start()
    log("You can view the running status through http://127.0.0.1:{}".format(port))

    with ProcessPoolExecutor(max_workers=glob.concurrency) as pool:
        futures = []
        for arg_group in glob.arg_group_list:
            # In some cases, not all tasks are fired.
            # Do not know why, but sleep(1) will work.
            sleep(1)
            futures.append(pool.submit(run_task, glob.executor, glob.runnable, arg_group))
        while True:
            done_num = 0
            for task_id, future in enumerate(futures):
                if future.running():
                    glob.arg_group_status[task_id] = "running"
                if future.done():
                    if future.result() == 0:
                        glob.arg_group_status[task_id] = "success"
                    else:
                        glob.arg_group_status[task_id] = "failed"
                    done_num += 1
            time.sleep(5)
            if done_num == len(futures):
                break


if __name__ == '__main__':
    main()
