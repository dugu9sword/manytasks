import importlib
import os
import random
import subprocess
import sys
import time
from argparse import ArgumentParser
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from threading import Thread
from time import sleep

import jstyleson

from manytasks import cuda_manager, shared
from manytasks.config_loader import init_config, load_config
from manytasks.extraction import extract_by_regex, extract_last_line, show
from manytasks.shared import Task, task2args, task2cmd
from manytasks.util import (Color, current_time, draw_logo, log, log_config,
                            show_task_list)
from manytasks.webui import app, available_port, init_gpu_handles


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
    run_mode.add_argument(dest='config_path',
                          action='store',
                          help='Specify the config path')
    run_mode.add_argument('--random',
                          dest='random_exe',
                          action='store_true',
                          help='Random execution')
    run_mode.add_argument('--latency',
                          dest='latency',
                          default=1,
                          type=int,
                          action='store',
                          help='Time (seconds) between execution of two tasks')
    run_mode.add_argument("--arxiv",
                          dest='arxiv',
                          default="",
                          help="where to save the logs (hdfs, email, etc.)")
    run_mode.add_argument(
        '--ui',
        dest='ui',
        action="store_true",
        help="Whether to start a web interface showing the status")
    # show the result
    show_mode = subparsers.add_parser("show")
    show_mode.add_argument(dest='log_path',
                           action='store',
                           help='Specify the log path')
    show_mode.add_argument("--rule",
                           dest='rule',
                           action='store',
                           default="",
                           help='Specify the extraction rule')

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
        elif opt.rule.endswith(".json"):
            show(opt.log_path,
                 extract_fn=partial(extract_by_regex,
                                    jstyleson.load(open(opt.rule))))
        elif opt.rule.endswith(".py"):
            sys.path.append(".")
            extract_fn = getattr(importlib.import_module(opt.rule[:-3]),
                                 "extract")
            show(opt.log_path, extract_fn=extract_fn)
        else:
            print("you must specify a legal rule file! (*.py, *.json)")
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
        shared.log_path = "{}.logs".format(opt.config_path[:-5])
    elif opt.config_path.endswith(".hjson"):
        shared.log_path = "{}.logs".format(opt.config_path[:-6])

    if os.path.exists(shared.log_path):
        override = input(
            "Logs for config {} exists, input [y] to override: ".format(
                opt.config_path))
        if override != 'y':
            print("ManyTasks Interupted.")
            exit()

    for p in Path(shared.log_path).glob("task-*.txt"):
        p.unlink()

    log_config("status", log_path=shared.log_path)
    load_config(opt.config_path)
    # if opt.random_exe:
    #     random.shuffle(shared.tasks)
    shared.task_status = ["pending"] * len(shared.tasks)
    for cuda_id in shared.cuda:
        cuda_manager.cuda_num[cuda_id] = 0


def run_task(executor, task: Task):
    def format_status(status, cuda_idx):
        if cuda_idx == -1:
            return "{:<30}".format(status)
        else:
            return "{:<38}".format(status)

    task_idx = shared.tasks.index(task)
    cuda_idx = cuda_manager.acquire_cuda()
    cuda_status = "| CUDA {}".format(cuda_idx) if cuda_idx != -1 else ""
    status = " START TASK {}/{} {}".format(shared.tasks.index(task), len(shared.tasks), cuda_status)
    
    log("{} [{}] {} : {}".format(
        Color.magenta("→"), 
        current_time(), 
        format_status(status, cuda_idx),
        task2cmd(task)))
    with open(
            "{}/task-{}.txt".format(shared.log_path, shared.tasks.index(task)),
            'w') as output:
        env = os.environ.copy()
        if cuda_idx != -1:
            env["CUDA_VISIBLE_DEVICES"] = str(cuda_idx)
        callee = executor.split(" ")
        callee.extend(task2args(task))
        shared.task_status[task_idx] = "running"
        ret = subprocess.call(callee, stdout=output, stderr=output, env=env)

        cuda_status = "| CUDA {}".format(cuda_idx) if cuda_idx != -1 else ""
        ret_status = "| RETURN {}".format(ret)
        status = "FINISH TASK {}/{} {} {}".format(shared.tasks.index(task), len(shared.tasks), cuda_status, ret_status)
        log_info = "{} [{}] {} : {}".format(
            Color.green("√") if ret == 0 else Color.red("×"), 
            current_time(),
            format_status(status, cuda_idx),
            task2cmd(task))
        log(log_info)
        cuda_manager.release_cuda(cuda_idx)
        return ret


def main():
    opt = parse_opt()
    preprocess(opt)
    draw_logo()
    show_task_list()

    # Start UI
    if opt.ui:
        log(">>>>>> Start web UI...")
        init_gpu_handles()
        port = available_port()
        ui_thread = Thread(target=app.run,
                           kwargs={
                               "host": "0.0.0.0",
                               "port": port
                           })
        ui_thread.daemon = True
        ui_thread.start()
        ui_url = Color.cyan("http://<YOUR IP ADDRESS>:{}".format(port))
        log(
            "You can view the running status through {}. ".format(ui_url),
            "Please make sure the port {} is open and not banned by the firewall!"
            .format(port))
        log()

    # Start Execution
    exe_order = list(range(len(shared.tasks)))
    if opt.random_exe:
        random.shuffle(exe_order)
    log(">>>>>> Start execution...")
    with ProcessPoolExecutor(max_workers=shared.concurrency) as pool:
        futures = []
        for idx in exe_order:
            # In some cases, not all tasks are fired.
            # Do not know why, but sleep(1) will work.
            futures.append(
                pool.submit(run_task, shared.executor, shared.tasks[idx]))
            sleep(opt.latency)
        while True:
            done_num = 0
            for task_id, future in enumerate(futures):
                if future.running():
                    shared.task_status[task_id] = "running"
                if future.done():
                    if future.result() == 0:
                        shared.task_status[task_id] = "success"
                    else:
                        shared.task_status[task_id] = "failed"
                    done_num += 1
            time.sleep(5)
            if done_num == len(futures):
                break

    log(Color.yellow("DONE!"))


if __name__ == '__main__':

    # log("Load task from {}".format(config_path),
    #     "- executor: {}".format(shared.executor),
    #     "- runnable: {}".format(shared.runnable),
    #     "- cuda: {}".format(str(shared.cuda)),
    #     "- concurrency: {}".format(shared.concurrency),
    #     "\n")

    main()
