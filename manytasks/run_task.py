from concurrent.futures import ProcessPoolExecutor
import subprocess
import time
import os
from threading import Thread
from argparse import ArgumentParser
from manytasks import shared
from manytasks.shared import Task, Arg, task2str, task2args
from manytasks.webui import app, available_port, init_gpu_handles
from tabulate import tabulate
from time import sleep
from pathlib import Path
import random
from manytasks.util import Color, log_config, log, current_time
from manytasks.config_loader import load_config, init_config
from manytasks import cuda_manager
from tailer import tail
import os
import zipfile
import re
from typing import List
from tabulate import tabulate
from collections import OrderedDict
import numpy as np
import importlib
import jstyleson
from functools import partial
import sys


def run_task(executor, task: Task):
    task_idx = shared.tasks.index(task)
    cuda_idx = cuda_manager.acquire_cuda()
    log("{} [{}] {} TASK {}/{} {} : {} {}".format(
        Color.magenta("→"), current_time(), "START",shared.tasks.index(task),
        len(shared.tasks),
        "(ON CUDA {})".format(cuda_idx) if cuda_idx != -1 else "", shared.executor,
        task2str(task)))
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
        log_info = "{} [{}] {} TASK {}/{} {} WITH RETURN ID {} : {} {}".format(
            Color.green("√") if ret == 0 else Color.red("×"), 
            current_time(), "FINISH", shared.tasks.index(task),
            len(shared.tasks),
            "(ON CUDA {})".format(cuda_idx) if cuda_idx != -1 else "", ret,
            shared.executor,
            task2str(task))
        log(log_info)
        cuda_manager.release_cuda(cuda_idx)
        return ret


def extract_last_line(text: List[str]):
    return {"last_line": text[-1].strip()}


def extract_by_regex(regex_dict, text: List[str]):
    ret = {}
    for k, v in regex_dict.items():
        data = []
        for line in text:
            if "include" in v and v["include"] not in line:
                continue
            found = re.search(v["regex"], line)
            if found:
                data.append(float(found.group(1)))
        reduce_fn = {
            "max": max,
            "min": min,
            "sum": sum
        }[v['reduce']]
        if len(data) == 0:
            ret[k] = None
        else:
            ret[k] = reduce_fn(data)   
    return ret

def show(log_path, extract_fn):
    tasks = {}
    status = open("{}/status.txt".format(log_path)).readlines()
    for line in status:
        found = re.search(r"TASK (\d+)/(\d+).*: (.*)", line)
        if found:
            idx = int(found.group(1))
            cmd = found.group(3)
            tasks[idx] = cmd
    tasks = OrderedDict(sorted(tasks.items()))
    table = []
    header = ["idx", "cmd"]
    ret = None
    for idx in tasks:
        ret = extract_fn(open("{}/task-{}.txt".format(log_path, idx)).readlines())
        table.append([idx, tasks[idx], *ret.values()])
    if ret:
        header.extend(list(ret.keys()))
        table.insert(0, header)
    result = tabulate(table)
    f = open("{}/result.txt".format(log_path), "w")
    print(result)
    print(result, file=f)
    


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
            show(opt.log_path, extract_fn=partial(extract_by_regex, jstyleson.load(open(opt.rule))))
        elif opt.rule.endswith(".py"):
            sys.path.append(".")
            extract_fn = getattr(importlib.import_module(opt.rule[:-3]), "extract")
            show(opt.log_path, extract_fn=extract_fn)
        else:
            print("you must specify a legal rule file! (*.py, *.json)")
        exit()
    return opt


def preprocess(opt):
    if not (opt.config_path.endswith(".hjson") or opt.config_path.endswith(".json")):
        opt.config_path += '.json'
    if not os.path.exists(opt.config_path):
        print("Config file {} not found.".format(opt.config_path))
        exit()

    shared.task_name = opt.config_path
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
    shared.executor, shared.cuda, shared.concurrency, shared.tasks = load_config(opt.config_path)
    # if opt.random_exe:
    #     random.shuffle(shared.tasks)
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

def compress(folder):
    zipped_name = '{}.zip'.format(folder)
    f = zipfile.ZipFile(zipped_name,'w',zipfile.ZIP_DEFLATED)
    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in filenames:
            f.write(os.path.join(dirpath,filename))
    f.close()
    return zipped_name

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
    if opt.arxiv != "":
        zipped_name = compress(shared.log_path)
        if opt.arxiv.startswith("hdfs://"):
            try:
                import tensorflow as tf
            except:
                print("You must install tensorflow to support hdfs!")
            tf.io.gfile.copy(zipped_name, opt.arxiv)
        elif opt.arxiv.startswith("mail://"):
            import json
            if not os.path.exists("mail.json"):
                print("mail.json not found.")
                exit(0)
            mail_config = json.load(open("mail.json"))

            import smtplib
            from email.mime.multipart import MIMEBase, MIMEMultipart
            from email.message import EmailMessage
            from email import encoders


            msg = MIMEMultipart()
            msg['Subject'] = '[MANYTASKS] {}'.format(zipped_name)
            msg['From'] = mail_config['from']
            msg['To'] = opt.arxiv[7:]

            part = MIMEBase('application', 'zip')
            part.set_payload(open(zipped_name, 'rb').read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=zipped_name)
            msg.attach(part)

            # Send the message via our own SMTP server.
            with smtplib.SMTP(mail_config['server']) as s:
                s.login(mail_config['user'], mail_config['password'])
                s.send_message(msg)
                s.quit()

        else:
            from shutil import copyfile
            copyfile(zipped_name, opt.arxiv)
        print("{} copied to {}".format(zipped_name, opt.arxiv))

if __name__ == '__main__':

    # log("Load task from {}".format(config_path),
    #     "- executor: {}".format(shared.executor),
    #     "- runnable: {}".format(shared.runnable),
    #     "- cuda: {}".format(str(shared.cuda)),
    #     "- concurrency: {}".format(shared.concurrency),
    #     "\n")

    main()
