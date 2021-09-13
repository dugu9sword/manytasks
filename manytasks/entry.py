import importlib
import os
import random
import re
import sys
import time
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from time import sleep

import yaml

from manytasks import cuda_manager, shared
from manytasks.config_loader import init_config, load_config
from manytasks.extraction import extract_by_regex, extract_last_line, show
from manytasks.task_runner import run_task
from manytasks.util import draw_logo, log, log_config, show_task_list


def parse_opt():
    usage = "You must specify a command, e.g. :\n" + \
        "\t1. Run `manytasks init` to create a config\n" + \
        "\t2. Run `manytasks run -h` to see how to run tasks\n" + \
        "\t3. Run `manytasks show -h` to see how to extract the results of tasks"

    parser = ArgumentParser(usage=usage)
    subparsers = parser.add_subparsers(dest='mode')

    # create a config file
    init_mode = subparsers.add_parser("init")

    # run a config file
    run_mode = subparsers.add_parser("run")
    run_mode.add_argument(               dest="config_path", action="store", default="", type=str,   help="Specify the config path")
    run_mode.add_argument("--output",    dest="output",      action="store", default="", type=str,   help="Specify the output path")
    run_mode.add_argument("--override",  dest="override",    action="store_true",                    help="Whether to force override existing logs")
    run_mode.add_argument("--resume",    dest="resume",      action="store_true",                    help="Whether to resume from existing logs")
    run_mode.add_argument("--random",    dest="random_exe",  action="store_true",                    help="Tasks are executed randomly")
    run_mode.add_argument("--latency",   dest="latency",     action="store", default=1,  type=int,   help="Time (seconds) between execution of two tasks")

    # show the result
    show_mode = subparsers.add_parser("show")
    show_mode.add_argument(              dest='log_path',    action='store',                         help='Specify the log path')
    show_mode.add_argument("--rule",     dest='rule',        action='store', default="",             help='Specify the extraction rule')

    opt = parser.parse_args()
    if opt.mode is None:
        print(usage)
        exit()
    elif opt.mode == "init":
        init_config()
        exit()
    elif opt.mode == 'show':
        if ".logs" not in opt.log_path:
            opt.log_path += '.logs'
        if opt.rule == "":
            show(opt.log_path, extract_fn=extract_last_line)
        elif opt.rule.endswith(".yaml"):
            show(opt.log_path, extract_fn=partial(extract_by_regex, yaml.safe_load(open(opt.rule))))
        elif opt.rule.endswith(".py"):
            sys.path.append(".")
            extract_fn = getattr(importlib.import_module(opt.rule[:-3]), "extract")
            show(opt.log_path, extract_fn=extract_fn)
        else:
            print("you must specify a legal rule file! (*.py, *.yaml)")
        exit()
    return opt


def preprocess(opt):
    if not opt.config_path.endswith(".json"):
        opt.config_path += '.json'
    if not os.path.exists(opt.config_path):
        print("Config file {} not found.".format(opt.config_path))
        exit()

    shared.config = opt.config_path
    if opt.config_path.endswith(".json"):
        if opt.output == "":
            shared.log_path = "{}.logs".format(opt.config_path[:-5])
        else:
            shared.log_path = "{}.logs".format(opt.output)

    shared.mode = shared.Mode.NORMAL
    if not opt.override and not opt.resume and os.path.exists(shared.log_path):
        act = input(
            "Logs for config {} exists, [o]verride or [r]esume (if possible)? "
            .format(opt.config_path))
        if act == "o":
            shared.mode = shared.Mode.OVERRIDE
        elif act == "r":
            shared.mode = shared.Mode.RESUME
        else:
            print("ManyTasks Interupted.")
            exit()

    if shared.mode == shared.Mode.OVERRIDE:
        for p in Path(shared.log_path).glob("task-*.txt"):
            p.unlink()

    log_config("status",
               log_path=shared.log_path,
               append=shared.mode == shared.Mode.RESUME)
    load_config(opt.config_path)
    shared.task_status = ["pending"] * len(shared.tasks)
    for cuda_id in shared.cuda:
        cuda_manager.cuda_num[cuda_id] = 0

    if shared.mode == shared.Mode.RESUME:
        is_task_status_line = False
        for line in open(Path(shared.log_path) / "status.txt"):
            if ">>>>>> Start execution..." in line:
                is_task_status_line = True
                continue
            if is_task_status_line:
                found = re.search(
                    r"FINISH TASK (\d+)/(\d+)\s+\|\s+RETURN\s+(-?\d+)", line)
                if found:
                    task_idx = int(found.group(1))
                    task_ret = int(found.group(3))
                    if int(task_ret) == 0:
                        shared.task_status[task_idx] = shared.Status.SUCCESS


def start_execution(opt):
    # Start Execution
    exe_order = list(range(len(shared.tasks)))
    if opt.random_exe:
        random.shuffle(exe_order)
    if shared.mode == shared.Mode.RESUME:
        log(">>>>>> Resume execution...")
    else:
        log(">>>>>> Start execution...")
    with ThreadPoolExecutor(max_workers=shared.concurrency) as pool:
        futures = []
        for idx in exe_order:
            # In some cases, not all tasks are fired.
            # Do not know why, but sleep(1) will work.
            if shared.task_status[idx] != shared.Status.SUCCESS:
                futures.append(
                    pool.submit(run_task, shared.executor, shared.tasks[idx]))
                sleep(opt.latency)
        while True:
            done_num = 0
            for task_id, future in enumerate(futures):
                if future.running():
                    shared.task_status[task_id] = shared.Status.RUNNING
                if future.done():
                    if future.result() == 0:
                        shared.task_status[task_id] = shared.Status.SUCCESS
                    else:
                        shared.task_status[task_id] = shared.Status.FAILED
                    done_num += 1
            time.sleep(5)
            if done_num == len(futures):
                break

    log("DONE!")


def main():
    opt = parse_opt()
    preprocess(opt)
    if shared.mode != shared.Mode.RESUME:
        draw_logo()
        show_task_list()
    start_execution(opt)


if __name__ == '__main__':
    main()
