import os
import subprocess

from manytasks import cuda_manager, shared
from manytasks.shared import Task, task2args, task2cmd
from manytasks.util import current_time, log


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
        # Color.magenta("→"), 
        "👉",
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
            # Color.green("√") if ret == 0 else Color.red("×"), 
            "✅" if ret == 0 else "❌",
            current_time(),
            format_status(status, cuda_idx),
            task2cmd(task))
        log(log_info)
        cuda_manager.release_cuda(cuda_idx)
        return ret