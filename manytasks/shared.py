from typing import NamedTuple, List

# Definition
Arg = NamedTuple("Arg", [("key", str),
                         ("value", object)])
Task = List[Arg]


def task2str(task: Task):
    return " ".join(list(map(lambda arg: "{}={}".format(arg.key, arg.value), task)))


# Variables
task_name = "<task>"
log_path = "<path>"
executor = "<python>"
runnable = "<main.py>"
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
