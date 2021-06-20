from typing import List, NamedTuple

# Definition
Arg = NamedTuple("Arg", [("key", str),
                         ("value", object)])
Task = List[Arg]

class Mode:
    NORMAL   = "NORMAL"
    OVERRIDE = "OVERRIDE"
    RESUME   = "RESUME"

class Status:
    SUCCESS  = "success"
    FAILED   = "failed"
    PENDING  = "pending"
    RUNNING  = "running"


def task2args(task: Task):
    buff = []
    for arg in task:
        if arg.key.startswith("__"):
            buff.append(arg.value)
        else:
            buff.append("{}".format(arg.key))
            buff.append("{}".format(arg.value))
    return buff

def task2str(task: Task):
    return " ".join(task2args(task))

def task2cmd(task: Task):
    return executor + " " + task2str(task)



# Variables
mode = "<mode>"
config_name = "<config>"
log_path = "<path>"
executor = "<python>"
cuda = [0, 1, 2]
concurrency = -1
tasks: List[Task] = [
# [Arg(key="--a", value=1), Arg(key="--b", value=2)],
# [Arg(key="--a", value=2), Arg(key="--b", value=2)],
# [Arg(key="--a", value=3), Arg(key="--b", value=2)],
# [Arg(key="--a", value=4), Arg(key="--b", value=2)],
# [Arg(key="--a", value=5), Arg(key="--b", value=2)],
# [Arg(key="--a", value=6), Arg(key="--b", value=2)]
]
task_status = [
# "success",
# "success",
# "pending",
# "running",
# "failed",
# "failed",
]
