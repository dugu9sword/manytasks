from typing import NamedTuple
from colorama import Fore, Back
from concurrent.futures import ProcessPoolExecutor
import subprocess
from multiprocessing import Manager
import time
import os
from typing import List
from argparse import ArgumentParser
import json


"""
LOGGING
"""
__log_path__ = "logs"


def log(*info, target='c'):
    assert target in ['c', 'f', 'cf', 'fc']
    info_str = str("\n".join(info))
    if 'c' in target:
        print(info_str)
    if 'f' in target:
        logger = globals()["__logger__"]
        logger.write("{}\n".format(info_str))
        logger.flush()


class Color(object):
    @staticmethod
    def red(s):
        return Fore.RED + str(s) + Fore.RESET

    @staticmethod
    def green(s):
        return Fore.GREEN + str(s) + Fore.RESET

    @staticmethod
    def yellow(s):
        return Fore.YELLOW + str(s) + Fore.RESET

    @staticmethod
    def blue(s):
        return Fore.BLUE + str(s) + Fore.RESET

    @staticmethod
    def magenta(s):
        return Fore.MAGENTA + str(s) + Fore.RESET

    @staticmethod
    def cyan(s):
        return Fore.CYAN + str(s) + Fore.RESET

    @staticmethod
    def white(s):
        return Fore.WHITE + str(s) + Fore.RESET

    @staticmethod
    def white_green(s):
        return Fore.WHITE + Back.GREEN + str(s) + Fore.RESET + Back.RESET


Arg = NamedTuple("Arg", [("key", str),
                         ("value", object)])
ArgGroup = List[Arg]
ArgGroupList = List[ArgGroup]


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


def log_config(filename, log_path=__log_path__, append=False):
    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)
    logger = open("{}/{}.txt".format(log_path, filename),
                  "a" if append else "w")
    globals()["__logger__"] = logger


def load_task(path="sample_task.json"):
    task = json.load(fp=open(path))
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


arg_lists: List = []
manager = Manager()
cuda_num = manager.dict()
cuda_lock = manager.Lock()
log_path: str


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
    cuda_idx = acquire_cuda()
    args_str = arg2str(arg_group)
    log("[{}] {} TASK {}/{} ON CUDA {} : {}".format(
        current_time(),
        "START",
        arg_lists.index(arg_group),
        len(arg_lists),
        cuda_idx,
        args_str), target='cf')
    with open("{}/task-{}.txt".format(log_path, arg_lists.index(arg_group)), 'w') as output:
        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = str(cuda_idx)
        callee = [executor, runnable]
        for arg in arg_group:
            callee.append("{}={}".format(arg.key, arg.value))
        subprocess.call(callee,
                        stdout=output,
                        stderr=output,
                        env=env)
        log("[{}] {} TASK {}/{} ON CUDA {} : {}".format(
            current_time(),
            "FINISH",
            arg_lists.index(arg_group),
            len(arg_lists),
            cuda_idx,
            args_str), target='cf')
        release_cuda(cuda_idx)


def main():
    parser = ArgumentParser()
    parser.add_argument('--task', dest='task_path', action='store', default="lstm.json",
                        help='Specify the task path, e.g. task.json')
    parser.add_argument('--override', dest='override', action='store', default=True, type=bool,
                        help='Whether to override existing logs')
    parsed_args = parser.parse_args()
    task_path = parsed_args.task_path
    override = parsed_args.override

    if not os.path.exists(task_path):
        print("Task {} not found.\n".format(task_path))
        exit()
    global log_path
    log_path = "{}.logs".format(task_path)
    if os.path.exists(log_path) and not override:
        print("Existing logs for task {} found, you may \n"
              "\t   1. rename the task to run\n"
              "\tor 2. back up the existing logs\n"
              "\tor 3. set the --override flag\n".format(task_path))
        exit()

    log_config("alchemist", log_path=log_path)
    executor, runnable, cuda, concurrency, parsed_confs = load_task(task_path)
    for cuda_id in cuda:
        cuda_num[cuda_id] = 0

    log("Load task from {}".format(task_path),
        "- executor: {}".format(executor),
        "- runnable: {}".format(runnable),
        "- cuda: {}".format(str(cuda)),
        "- concurrency: {}".format(concurrency),
        target='cf')

    for config in parsed_confs:
        arg_lists.extend(gen_arg_list(config))

    log("Mappings(idx->args)", target='cf')
    for idx, arg_group in enumerate(arg_lists):
        log("\t{} : {}".format(idx, arg2str(arg_group)), target='cf')

    with ProcessPoolExecutor(max_workers=concurrency) as pool:
        futures = []
        for arg_group in arg_lists:
            futures.append(pool.submit(run_task, executor, runnable, arg_group))
        for future in futures:
            future.done()


if __name__ == '__main__':
    main()