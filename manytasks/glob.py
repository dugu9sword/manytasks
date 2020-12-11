from typing import NamedTuple, List
from multiprocessing import Manager

# Definition
Arg = NamedTuple("Arg", [("key", str),
                         ("value", object)])
ArgGroup = List[Arg]
ArgGroupList = List[ArgGroup]

task_name = "<task>"

log_path = "<path>"

executor = "<python>"
runnable = "<main.py>"
cuda = [0, 1, 2]
concurrency = -1

manager = Manager()

# arg_group_list = manager.list()

# arg_group_status = manager.list()

arg_group_list: ArgGroupList = [
# [Arg(key="--a", value=1), Arg(key="--b", value=2)],
# [Arg(key="--a", value=2), Arg(key="--b", value=2)],
# [Arg(key="--a", value=3), Arg(key="--b", value=2)],
# [Arg(key="--a", value=4), Arg(key="--b", value=2)],
# [Arg(key="--a", value=5), Arg(key="--b", value=2)],
# [Arg(key="--a", value=6), Arg(key="--b", value=2)]
]

arg_group_status = [
# "success",
# "success",
# "pending",
# "running",
# "failed",
# "failed",
]
