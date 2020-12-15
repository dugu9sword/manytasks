from concurrent.futures import ProcessPoolExecutor
import subprocess
import time
import os
from threading import Thread
from argparse import ArgumentParser
from manytasks import shared
from manytasks.shared import Task, Arg, task2str
from manytasks.webui import app, available_port, init_gpu_handles
from tabulate import tabulate
from time import sleep
from pathlib import Path
import random
from manytasks.util import Color, log_config, log, current_time
from manytasks.config_loader import load_config, init_config
from manytasks import cuda_manager
from tailer import tail


def run_task(executor, runnable, task: Task):
    task_idx = shared.tasks.index(task)
    cuda_idx = cuda_manager.acquire_cuda()
    log("[{}] {} TASK {}/{} {} : {}".format(
        current_time(), Color.magenta("START"), shared.tasks.index(task),
        len(shared.tasks),
        "(ON CUDA {})".format(cuda_idx) if cuda_idx != -1 else "",
        task2str(task)))
    with open(
            "{}/task-{}.txt".format(shared.log_path, shared.tasks.index(task)),
            'w') as output:
        env = os.environ.copy()
        if cuda_idx != -1:
            env["CUDA_VISIBLE_DEVICES"] = str(cuda_idx)
        callee = [executor, runnable]
        for arg in task:
            callee.append("{}={}".format(arg.key, arg.value))
        shared.task_status[task_idx] = "running"
        ret = subprocess.call(callee, stdout=output, stderr=output, env=env)
        log_info = "[{}] {} TASK {}/{} {} WITH RETURN ID {} : {}".format(
            current_time(), "FINISH", shared.tasks.index(task),
            len(shared.tasks),
            "(ON CUDA {})".format(cuda_idx) if cuda_idx != -1 else "", ret,
            task2str(task))
        log(Color.green(log_info) if ret == 0 else Color.red(log_info))
        cuda_manager.release_cuda(cuda_idx)
        return ret


def parse_opt():
    usage = "You must specify a command, e.g. :\n" + \
        "\t1. Run `manytasks init` to create a config\n" + \
        "\t2. Run `manytasks run -h` to see how to run tasks\n" + \
        "\t3. If you print the result at the end of a task, run `manytasks show -h` to see how to show results of each task"

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
        infos = []
        found_index = False
        for line in open("{}/status.txt".format(opt.log_path)):
            if line.strip() == '>>>>>> Show the task list...':
                found_index = True
            if line.strip() == '>>>>>> Start execution...':
                break
            if found_index:
                infos.append(line)
                # print(line)
        print("".join(infos))

        print('>>>>>> Show the last line...')
        for i in range(len(infos) - 5):
            print(tail(open("{}/task-{}.txt".format(opt.log_path, i)), lines=1)[0])

        exit()
    return opt


def preprocess(opt):
    if ".hjson" not in opt.config_path:
        opt.config_path += '.hjson'
    if not os.path.exists(opt.config_path):
        print("Config file {} not found.".format(opt.config_path))
        exit()

    shared.task_name = opt.config_path
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
    shared.executor, shared.runnable, shared.cuda, shared.concurrency, shared.tasks = load_config(
        opt.config_path)
    if opt.random_exe:
        random.shuffle(shared.tasks)
    shared.task_status = ["pending"] * len(shared.tasks)
    for cuda_id in shared.cuda:
        cuda_manager.cuda_num[cuda_id] = 0


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


def show_task_list():
    log(">>>>>> Show the task list...")
    keys = []
    for task in shared.tasks:
        for arg in task:
            if arg.key not in keys:
                keys.append(arg.key)

    header = ['idx'] + keys
    # header = list(map(Color.cyan, header))
    table = [header]
    for idx, task in enumerate(shared.tasks):
        # log("\t{} : {}".format(idx, arg2str(arg_group)), target='cf')
        values = []
        for key in keys:
            found = False
            for arg in task:
                if arg.key == key:
                    found = True
                    values.append(arg.value)
                    break
            if not found:
                values.append("-")
        table.append([idx] + values)
    log(tabulate(table))
    log()


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
    log(">>>>>> Start execution...")
    with ProcessPoolExecutor(max_workers=shared.concurrency) as pool:
        futures = []
        for task in shared.tasks:
            # In some cases, not all tasks are fired.
            # Do not know why, but sleep(1) will work.
            sleep(1)
            futures.append(
                pool.submit(run_task, shared.executor, shared.runnable, task))
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
