import os
import subprocess
import time
from collections import defaultdict

from manytasks import cuda_manager
from manytasks.shared import Settings, Task, TaskPool
from manytasks.util import current_time, log


def run_task(executor, task: Task, latency=None, timeout=None):
    settings = Settings()
    taskpool = TaskPool()
    
    if latency:
        time.sleep(latency)

    with open(
            "{}/task-{}.txt".format(settings.log_path, taskpool.index(task)),
            'w') as output:
        cuda_idx = cuda_manager.acquire_cuda()
        env = os.environ.copy()
        if cuda_idx != -1:
            env["CUDA_VISIBLE_DEVICES"] = str(cuda_idx)
        callee = executor.split(" ")
        callee.extend(task.to_callable_args())

        width = len(taskpool) // 10 + 1
        task_info = "TASK {:>{width}}/{:>{width}}".format(taskpool.index(task), len(taskpool), width=width)

        # process starting...
        p = subprocess.Popen(callee, stdout=output, stderr=output, env=env)
        cuda_status = "| CUDA {}".format(cuda_idx) if cuda_idx != -1 else ""
        pid_status = "| PID {:<8}".format(p.pid)
        status = " START {} {} {}".format(task_info, cuda_status, pid_status)
        log("{} [{}] {} : {}".format(
            "👉",
            current_time(), 
            status,
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
        ret_status = "| RET {:<8}".format(ret)
        status = "FINISH {} {} {}".format(task_info, cuda_status, ret_status)
        log("{} [{}] {} : {}".format(
            defaultdict(lambda: "❌", {0: "✅", -1926: "🐸"})[ret],
            current_time(),
            status,
            task.to_finalized_cmd()))

        cuda_manager.release_cuda(cuda_idx)
        return ret