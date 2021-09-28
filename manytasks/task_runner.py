import os
import subprocess
import time
from collections import defaultdict

from manytasks import cuda_manager, shared
from manytasks.shared import Task
from manytasks.util import current_time, log


def run_task(executor, task: Task, latency=None, timeout=None):
    def format_status(status, cuda_idx):
        if cuda_idx == -1:
            return "{:<30}".format(status)
        else:
            return "{:<38}".format(status)
    
    if latency:
        time.sleep(latency)

    with open(
            "{}/task-{}.txt".format(shared.log_path, shared.tasks.index(task)),
            'w') as output:
        cuda_idx = cuda_manager.acquire_cuda()
        env = os.environ.copy()
        if cuda_idx != -1:
            env["CUDA_VISIBLE_DEVICES"] = str(cuda_idx)
        callee = executor.split(" ")
        callee.extend(task.to_callable_args())

        width = len(shared.tasks) % 10
        task_info = "TASK {:>{width}}/{:>{width}}".format(shared.tasks.index(task), len(shared.tasks), width=width)

        # process starting...
        p = subprocess.Popen(callee, stdout=output, stderr=output, env=env)
        cuda_status = "| CUDA {}".format(cuda_idx) if cuda_idx != -1 else ""
        pid_status = "| PID {}".format(p.pid)
        status = " START {} {} {}".format(task_info, cuda_status, pid_status)
        log("{} [{}] {} : {}".format(
            "👉",
            current_time(), 
            format_status(status, cuda_idx),
            task.to_finalized_cmd()))

        # process ending...
        if timeout is None:
            ret = p.wait(timeout)
        else:
            timeout_num, timeout_as_success = timeout
            try:
                ret = p.wait(timeout=timeout_num)
            except subprocess.TimeoutExpired:
                if timeout_as_success:
                    ret = 0
                else:
                    ret = -1926
        cuda_status = "| CUDA {}".format(cuda_idx) if cuda_idx != -1 else ""
        ret_status = "| RET {}".format(ret)
        status = "FINISH {} {} {}".format(task_info, cuda_status, ret_status)
        log("{} [{}] {} : {}".format(
            defaultdict(lambda: "❌", {0: "✅", -1926: "🐸"})[ret],
            current_time(),
            format_status(status, cuda_idx),
            task.to_finalized_cmd()))

        cuda_manager.release_cuda(cuda_idx)
        return ret