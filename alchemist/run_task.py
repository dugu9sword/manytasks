from alchemist.task_loader import load_task
from alchemist.config_iterator import gen_arg_list
from concurrent.futures import ProcessPoolExecutor
import subprocess
from multiprocessing import Manager
import time
import os
from alchemist.log import log, log_config
from typing import List
from argparse import ArgumentParser

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
    args = arg2str(arg_group)
    log("[{}] {} TASK {}/{} ON CUDA {} : {}".format(
        current_time(),
        "START",
        arg_lists.index(arg_group),
        len(arg_lists),
        cuda_idx,
        args), target='cf')
    with open("{}/task-{}.txt".format(log_path, arg_lists.index(arg_group)), 'w') as output:
        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = str(cuda_idx)
        subprocess.call([executor, runnable, args],
                        stdout=output,
                        stderr=output,
                        env=env)
        log("[{}] {} TASK {}/{} ON CUDA {} : {}".format(
            current_time(),
            "FINISH",
            arg_lists.index(arg_group),
            len(arg_lists),
            cuda_idx,
            args), target='cf')
        release_cuda(cuda_idx)


def main():
    parser = ArgumentParser()
    parser.add_argument('--task', dest='task_path', action='store', default="sample_task.json",
                        help='Specify the task path, e.g. sample_task.json')
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
