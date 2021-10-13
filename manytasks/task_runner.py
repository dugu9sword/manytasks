import math
import os
import re
import shutil
import subprocess
import time
from collections import defaultdict
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path

from manytasks import cuda_manager
from manytasks.defs import Mode, Status, TaskPool
from manytasks.util import (current_time, draw_logo, log, log_config,
                            show_task_list)


def run_task(opt, taskpool: TaskPool, task_idx):
    if opt.latency:
        time.sleep(opt.latency)
    task = taskpool[task_idx]

    with open("{}/task-{}.txt".format(opt.log_path, task_idx), 'w') as output:
        cuda_idx = cuda_manager.acquire_cuda()
        env = os.environ.copy()
        if cuda_idx != -1:
            env["CUDA_VISIBLE_DEVICES"] = str(cuda_idx)
        callee = task.executor + task.to_callable_args()

        width = int(math.log10(len(taskpool))) + 1
        task_info = "TASK {:>{width}}/{:>{width}}".format(taskpool.index(task),
                                                          len(taskpool),
                                                          width=width)

        # process starting...
        p = subprocess.Popen(callee, stdout=output, stderr=output, env=env)
        cuda_status = "| CUDA {}".format(cuda_idx) if cuda_idx != -1 else ""
        pid_status = "| PID {:<8}".format(p.pid)
        status = " START {} {} {}".format(task_info, cuda_status, pid_status)
        log("{} [{}] {} : {}".format("👉", current_time(), status,
                                     task.to_finalized_cmd()))

        # process ending...
        if opt.timeout is None:
            ret = p.wait()
        else:
            timeout_num, timeout_as_success = opt.timeout
            try:
                ret = p.wait(timeout=timeout_num)
            except subprocess.TimeoutExpired:
                if timeout_as_success:
                    ret = 0
                else:
                    ret = -1926
        cuda_status = "| CUDA {}".format(cuda_idx) if cuda_idx != -1 else ""
        ret_status = "| RET {:<8}".format(ret)
        status = "FINISH {} {} {}".format(task_info, cuda_status, ret_status)
        log("{} [{}] {} : {}".format(
            defaultdict(lambda: "❌", {
                0: "✅",
                -1926: "🐸"
            })[ret], current_time(), status, task.to_finalized_cmd()))

        cuda_manager.release_cuda(cuda_idx)
        return ret


def start_execution(opt, taskpool: TaskPool):
    if opt.random_exe:
        taskpool.shuffle()
    futures = {}
    with ThreadPoolExecutor(opt.concurrency) as executor:
        while not taskpool.finished():
            done_ids = []
            for fid, future in futures.items():
                if future.running():
                    taskpool[fid].status = Status.RUNNING
                if future.done():
                    if future.result() == 0:
                        taskpool[fid].status = Status.SUCCESS
                    else:
                        taskpool[fid].status = Status.FAILED
                    done_ids.append(fid)
            for fid in done_ids:
                futures.pop(fid)
            while True:
                if not taskpool.has_next() or len(futures) == opt.concurrency:
                    break
                next_idx, next_task = taskpool.get_next_task()
                if next_task.status != Status.SUCCESS:
                    futures[next_idx] = executor.submit(run_task, opt, taskpool, next_idx)
    log("DONE! (total={}, success={}, fail={})".format(len(taskpool), taskpool.num_success(), taskpool.num_failed()))

def prepare_log_directory(opt, taskpool):
    if not os.path.exists(opt.log_path):
        os.makedirs(opt.log_path)

    shutil.copy(opt.config_path, os.path.join(opt.log_path, "config.json"))

    log_config("status",
               log_path=opt.log_path,
               append=opt.run_mode == Mode.RESUME)

    if opt.run_mode == Mode.RESUME:
        log(">>>>>> Resume execution...")
    else:
        draw_logo()
        show_task_list(taskpool)
        log(">>>>>> Start execution...")

    if opt.run_mode == Mode.OVERRIDE:
        for p in Path(opt.log_path).glob("task-*.txt"):
            p.unlink()
    elif opt.run_mode == Mode.RESUME:
        is_task_status_line = False
        for line in open(Path(opt.log_path) / "status.txt"):
            if ">>>>>> Start execution..." in line:
                is_task_status_line = True
                continue
            if is_task_status_line:
                found = re.search(
                    r"FINISH TASK\s*(\d+)/.*RET\s*(-?\d+)", line)
                if found:
                    task_idx = int(found.group(1))
                    task_ret = int(found.group(2))
                    if int(task_ret) == 0:
                        taskpool[task_idx].status = Status.SUCCESS
