import os
import re
import shutil
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from manytasks import cuda_manager
from manytasks.config_loader import load_config
from manytasks.extraction import show
from manytasks.shared import Mode, Settings, Status, TaskPool
from manytasks.task_runner import run_task
from manytasks.util import (draw_logo, init_config, init_rule, log, log_config,
                            show_task_list)


def parse_opt():
    usage = "You must specify a command, e.g. :\n" + \
        "\t1. Run `manytasks init` to create a config/rule\n" + \
        "\t2. Run `manytasks run -h` to see how to run tasks\n" + \
        "\t3. Run `manytasks show -h` to see how to extract the results of tasks"

    parser = ArgumentParser(usage=usage)
    subparsers = parser.add_subparsers(dest='mode')

    # create a config file
    init_mode = subparsers.add_parser("init")
    init_mode.add_argument(              dest="template",    action="store", default="",   type=str,   help="Generate a template file")
    
    # run a config file
    run_mode = subparsers.add_parser("run")
    run_mode.add_argument(               dest="config_path", action="store", default="",   type=str,   help="Specify the config path")
    run_mode.add_argument("--output",    dest="output",      action="store", default="",   type=str,   help="Specify the output path")
    run_mode.add_argument("--override",  dest="override",    action="store_true",                      help="Whether to force override existing logs")
    run_mode.add_argument("--resume",    dest="resume",      action="store_true",                      help="Whether to resume from existing logs")
    run_mode.add_argument("--random",    dest="random_exe",  action="store_true",                      help="Tasks are executed randomly")
    run_mode.add_argument("--latency",   dest="latency",     action="store", default=1,    type=int,   help="Time (seconds) between execution of two tasks")
    run_mode.add_argument("--timeout",   dest="timeout",     action="store", default=None, type=str,   help="Timeout of a task (9S, 5m, 3H, 4d, etc.)")

    # show the result
    show_mode = subparsers.add_parser("show")
    show_mode.add_argument(              dest='log_path',    action='store',                           help='Specify the log path')
    show_mode.add_argument("--rule",     dest='rule_path',   action='store', default="",               help='Specify the extraction rule')

    opt = parser.parse_args()
    if opt.mode is None:
        print(usage)
        exit()
    elif opt.mode == "init":
        if opt.template == "config":
            init_config()
        elif opt.template == "rule":
            init_rule()
        else:
            print(usage)
        exit()
    elif opt.mode == 'show':
        if ".logs" not in opt.log_path:
            opt.log_path += '.logs'
        load_config(os.path.join(opt.log_path, "config.json"))
        if not opt.rule_path.endswith(".yaml"):
            opt.rule_path += '.yaml'
        if not os.path.exists(opt.rule_path):
            print("you must specify a legal rule file! (*.yaml)")
            exit()
        show(opt.log_path, regex_rule=yaml.safe_load(open(opt.rule_path)))
        exit()
    return opt


def preprocess(opt):
    settings = Settings()
    if not opt.config_path.endswith(".json"):
        opt.config_path += '.json'
    if not os.path.exists(opt.config_path):
        print("Config file {} not found.".format(opt.config_path))
        exit()

    settings.config = opt.config_path
    if opt.config_path.endswith(".json"):
        if opt.output == "":
            settings.log_path = "{}.logs".format(opt.config_path[:-5])
        else:
            settings.log_path = "{}.logs".format(opt.output)

    assert not (opt.resume and opt.override), "--resume and --override should not be set at the same time!"
    if opt.resume:
        settings.mode = Mode.RESUME
    elif opt.override:
        settings.mode = Mode.OVERRIDE
    elif (not opt.override) and (not opt.resume) and os.path.exists(settings.log_path):
        act = input(
            "Logs for config {} exists, [o]verride or [r]esume (if possible)? "
            .format(opt.config_path))
        if act == "o":
            settings.mode = Mode.OVERRIDE
        elif act == "r":
            settings.mode = Mode.RESUME
        else:
            print("ManyTasks Interupted.")
            exit()
    else:
        settings.mode = Mode.NORMAL

    shutil.copy(opt.config_path, os.path.join(settings.log_path, "config.json"))

    if opt.timeout is not None:
        timeout_num = int(opt.timeout[:-1])
        timeout_unit = opt.timeout[-1]
        if timeout_unit in "Ss":
            opt.timeout = (timeout_num, timeout_unit == "S")
        elif timeout_unit in "Mm":
            opt.timeout = (timeout_num * 60, timeout_unit == "M")
        elif timeout_unit in "Hh":
            opt.timeout = (timeout_num * 3600, timeout_unit == "H")     
        elif timeout_unit in "Dd":
            opt.timeout = (timeout_num * 3600 * 24, timeout_unit == "D")
        else:
            raise Exception

    if settings.mode == Mode.OVERRIDE:
        for p in Path(settings.log_path).glob("task-*.txt"):
            p.unlink()

    log_config("status",
               log_path=settings.log_path,
               append=settings.mode == Mode.RESUME)
    load_config(opt.config_path)
    for cuda_id in settings.cuda:
        cuda_manager.cuda_num[cuda_id] = 0

    taskpool = TaskPool()
    if settings.mode == Mode.RESUME:
        is_task_status_line = False
        for line in open(Path(settings.log_path) / "status.txt"):
            if ">>>>>> Start execution..." in line:
                is_task_status_line = True
                continue
            if is_task_status_line:
                found = re.search(r"FINISH TASK\s*(\d+)/(\d+)\s*\|\s*RET\s*(-?\d+)", line)
                if found:
                    task_idx = int(found.group(1))
                    task_ret = int(found.group(3))
                    if int(task_ret) == 0:
                        taskpool[task_idx].status = Status.SUCCESS


def start_execution(opt):
    taskpool = TaskPool()
    settings = Settings()
    if opt.random_exe:
        taskpool.shuffle()
    if settings.mode == Mode.RESUME:
        log(">>>>>> Resume execution...")
    else:
        log(">>>>>> Start execution...")
    with ThreadPoolExecutor(max_workers=settings.concurrency) as pool:
        futures = []
        # fill the pool with some tasks
        while True:
            if not taskpool.has_next() or len(futures) == settings.concurrency:
                break
            next_task = taskpool.get_next_task()
            if next_task.status != Status.SUCCESS:
                futures.append(
                    pool.submit(run_task, settings.executor, next_task, opt.latency, opt.timeout))

        # add more tasks to the pool
        while True:
            done_num = 0
            new_futures = []
            for task_id, future in enumerate(futures):
                if future.running():
                    taskpool[task_id].status = Status.RUNNING
                if future.done():
                    if future.result() == 0:
                        taskpool[task_id].status = Status.SUCCESS
                    else:
                        taskpool[task_id].status = Status.FAILED
                    done_num += 1
                    if taskpool.has_next():
                        next_task = taskpool.get_next_task()
                        new_futures.append(pool.submit(run_task, settings.executor, next_task, opt.latency, opt.timeout))
            futures.extend(new_futures)
            # time.sleep(5)
            if done_num == len(futures):
                break

    log("DONE!")


def main():
    settings = Settings()
    opt = parse_opt()
    preprocess(opt)
    if settings.mode != Mode.RESUME:
        draw_logo()
        show_task_list()
    start_execution(opt)


if __name__ == '__main__':
    main()
