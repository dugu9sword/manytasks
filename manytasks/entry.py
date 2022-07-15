import multiprocessing
import os
from argparse import ArgumentParser
from pathlib import Path

import jstyleson
import psutil
import yaml

from manytasks import cuda_manager
from manytasks.defs import Mode
from manytasks.log_extractor import show
from manytasks.task_runner import prepare_log_directory, start_execution
from manytasks.taskpool_loader import load_taskpool
from manytasks.util import (exists_fast_fail, init_config, init_rule,
                            safe_append, safe_cut, show_task_list)


def parse_opt():
    # yapf: disable
    # usage = "You must specify a command, e.g. :\n" + \
    #     "\t1. Run `manytasks init -h` to see how to create a config/rule\n" + \
    #     "\t2. Run `manytasks run -h` to see how to run tasks\n" + \
    #     "\t3. Run `manytasks show -h` to see how to extract the results of tasks"

    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode")

    # create a config/rule file
    init_mode = subparsers.add_parser("init")
    init_mode.add_argument(                    dest="template",    action="store", default="",   type=str,   choices=["config", "rule"],
                            help="Generate a template file, `config` for running tasks and `rule` for log extraction.")

    # run a config file
    run_mode = subparsers.add_parser("run")
    run_mode.add_argument(                     dest="config_path", action="store", default="",   type=str,   
                            help="Specify the config path such as 'config_name.json', " 
                                + "where the suffix '.json' can be omitted in case that it is in the current directory.")
    run_mode.add_argument("--log-path",  "-p", dest="log_path",    action="store", default="",   type=str,   
                            help="Specify the log path. " 
                                + "The path will be 'config_name.logs' in case that it is not specified.")
    run_mode.add_argument("--override",  "-o", dest="override",    action="store_true",                      
                            help="Whether to force override existing logs. ")
    run_mode.add_argument("--resume",    "-r", dest="resume",      action="store_true",                      
                            help="Whether to resume from existing logs. "
                                + "Only tasks that are failed will be runned again.")
    run_mode.add_argument("--random-exe","-e", dest="random_exe",  action="store_true",                      
                            help="Whether tasks are executed randomly. ")
    run_mode.add_argument("--dry",       "-d", dest="dry",         action="store_true",                      
                            help="Just print all tasks to run instead of running them. ")
    run_mode.add_argument("--latency",   "-l", dest="latency",     action="store", default=1,    type=int,   
                            help="Time (seconds) between execution of two tasks ." 
                                + "This can be useful if executing tasks too frequently will cause some errors, \n"
                                + "such as downloading many files from a server too frequently.")
    run_mode.add_argument("--timeout",   "-t", dest="timeout",     action="store", default=None, type=str,   
                            help="Timeout of a task (9S, 5m, 3H, 4d, etc.). "
                               + "This can be useful if a task is not expected to run for too long time. "
                               + "The 'early stop' strategy can help you explore more settings. "
                               + "Note that the upper case (1S, 1M, 1H, 1D) denotes that a timeout is considered as SUCESS, "
                               + "while the lower case (1s, 1m, 1h, 1d) denotes that it is considered as FAILED. ")

    # show the result
    show_mode = subparsers.add_parser("show")
    show_mode.add_argument(              dest="log_path",    action="store",                           
                            help="Specify the log path such as 'config_name.logs', where the suffix '.logs' can be omitted")
    show_mode.add_argument("--rule",     dest="rule_path",   action="store", default="",               
                            help="Specify the extraction rule such as 'rule.yaml', where the suffix '.yaml' can be omitted. ")
    # yapf: enable

    opt = parser.parse_args()

    if opt.mode is None:
        parser.print_help()
        print("\n\n====== manytasks init ======\n")
        init_mode.print_help()
        print("\n\n====== manytasks run  ======\n")
        run_mode.print_help()
        print("\n\n====== manytasks show ======\n")
        show_mode.print_help()
    return opt


def preprocess(opt):
    # Rewrite opt.log_path
    if opt.log_path == "":
        opt.log_path = safe_append(safe_cut(opt.config_path, ".json"), ".logs")
    else:
        opt.log_path = safe_append(opt.log_path, ".logs")

    # Add opt.run_mode
    assert not (
        opt.resume and opt.override
    ), "--resume and --override should not be set at the same time!"
    if opt.resume:
        opt.run_mode = Mode.RESUME
    elif opt.override:
        opt.run_mode = Mode.OVERRIDE
    elif (not opt.override) and (not opt.resume) and os.path.exists(
            opt.log_path):
        act = input(
            "Logs for config {} exists, [o]verride or [r]esume (if possible)? "
            .format(opt.config_path))
        if act == "o":
            opt.run_mode = Mode.OVERRIDE
        elif act == "r":
            opt.run_mode = Mode.RESUME
        else:
            print("ManyTasks Interupted.")
            exit()
    else:
        opt.run_mode = Mode.NORMAL

    # Rewrite opt.timeout
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

    # Initialze cuda manager
    config = jstyleson.load(fp=open(opt.config_path))
    cuda = config["cuda"]
    opt.cuda = cuda
    assert isinstance(cuda, list) or cuda == -1
    if cuda != -1 and psutil.WINDOWS:
        print("CUDA shoule be -1 on windows")
        exit()
    if cuda == -1 or (isinstance(cuda, list) and len(cuda) == 0):
        pass
    else:
        for cuda_id in cuda:
            cuda_manager.num_tasks_on_cuda[cuda_id] = 0
    opt.cuda_per_task = int(config["cuda_per_task"])

    # Add opt.concurrency
    if config["concurrency"] == "#CUDA":
        if cuda[0] != -1:
            opt.concurrency = len(cuda)
        else:
            print(
                "You must specify which CUDA devices you want to use if concurrency is set to #CUDA."
            )
            exit()
    elif config["concurrency"] == "#CPU":
        opt.concurrency = max(1, multiprocessing.cpu_count() - 1)
    else:
        opt.concurrency = int(config["concurrency"])


def main():
    opt = parse_opt()

    if opt.mode == "init":
        if opt.template == "config":
            init_config()
        elif opt.template == "rule":
            init_rule()
        else:
            print("`manytasks init` only accept args `config` or `rule`")

    elif opt.mode == "run":
        opt.config_path = safe_append(opt.config_path, ".json")
        exists_fast_fail(opt.config_path)

        taskpool = load_taskpool(opt.config_path)
        if opt.dry:
            show_task_list(taskpool, target="c")
        else:
            preprocess(opt)
            prepare_log_directory(opt, taskpool)
            start_execution(opt, taskpool)

    elif opt.mode == "show":
        opt.log_path = safe_append(opt.log_path, ".logs")
        exists_fast_fail(opt.log_path)
        opt.rule_path = safe_append(opt.rule_path, ".yaml")
        exists_fast_fail(opt.rule_path)

        taskpool = load_taskpool(Path(opt.log_path) / "config.json")
        show(opt, taskpool, regex_rule=yaml.safe_load(open(opt.rule_path)))


if __name__ == "__main__":
    main()
