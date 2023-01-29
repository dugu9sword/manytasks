import random
import re
from typing import List


# Definition
class Arg:
    def __init__(self, key, value) -> None:
        self.key: str = key
        self.value = value

    def __repr__(self) -> str:
        return "Arg({}={})".format(self.key, self.value)


class Task:
    def __init__(self, executor, args) -> None:
        self.executor: List[str] = executor
        self.args: List[Arg] = args
        self.status = Status.PENDING

    @property
    def keys(self):
        ret = []
        for arg in self.args:
            ret.append(arg.key)
        return ret

    @property
    def values(self):
        ret = []
        for arg in self.args:
            ret.append(arg.value)
        return ret

    def smart_key(self, key):
        if re.match(r"\d+", key):
            return f"__{key}"
        if re.match(r"\d+\.\d+", key):
            return f"__{key}"
        if f"-{key}" in self.keys:
            return f"-{key}"
        if f"--{key}" in self.keys:
            return f"--{key}"
        return None

    def __contains__(self, key):
        return self.smart_key(key) is not None

    def __setitem__(self, key, value):
        self.args[self.keys.index(key)].value = value

    def __getitem__(self, key):
        return self.args[self.keys.index(key)].value

    def __iter__(self):
        return iter(self.args)

    def __repr__(self):
        return "Task(Arg={}, Status={})".format(self.to_finalized_args(),
                                                self.status)

    def to_callable_args(self):
        """
            Return: ["arg0", "--key1", "arg1", "--key2", "arg2"]
        """
        buff = []
        for arg in self.args:
            if arg.key.startswith("__"):
                buff.append(arg.value)
            elif arg.value == Reserved.ON:
                buff.append(arg.key)
            elif arg.value == Reserved.OFF:
                pass
            else:
                buff.append("{}".format(arg.key))
                buff.append("{}".format(arg.value))
        return buff

    def to_finalized_args(self):
        """
            Return: "arg0 --key1 arg1 --key2 --arg2"
        """
        return " ".join(self.to_callable_args())

    def to_finalized_cmd(self):
        """
            Return: "python3 script.py arg0 --key1 arg1 --key2 --arg2"
        """
        return " ".join(self.executor) + " " + self.to_finalized_args()


class Mode:
    NORMAL = "NORMAL"
    OVERRIDE = "OVERRIDE"
    RESUME = "RESUME"


class Status:
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    RUNNING = "RUNNING"


class Reserved:
    ON = "$_ON_"
    OFF = "$_OFF_"

    @classmethod
    def symbol(cls, word):
        return {
            cls.ON: "✔",
            cls.OFF: "-", # or use "☐"?
        }[word]

    @classmethod
    def is_reserved(cls, word):
        return word in [cls.ON, cls.OFF]


class TaskPool:
    def __init__(self):
        # information
        self._tasks: List[Task]
        self._keys: List[str]

        # execution order
        self._order: List[int]
        self._next_order_idx: int

    def set_tasks(self, tasks: List[Task]):
        self._tasks = tasks
        self._keys = []
        for task in self._tasks:
            for arg in task:
                if arg.key not in self._keys:
                    self._keys.append(arg.key)

        self._order = list(range(len(tasks)))
        self._next_order_idx = 0

    @property
    def keys(self):
        return self._keys

    def index(self, task):
        return self._tasks.index(task)

    def __iter__(self):
        return iter(self._tasks)

    def __len__(self):
        return len(self._tasks)

    def __getitem__(self, index):
        return self._tasks[index]

    def has_next(self):
        return self._next_order_idx + 1 <= len(self._order)

    def get_next_task(self):
        ret = self._order[self._next_order_idx], self._tasks[self._order[self._next_order_idx]]
        self._next_order_idx += 1
        return ret

    def shuffle(self, start=0, stop=None):
        i = start
        if stop is None:
            stop = len(self)
        while (i < stop - 1):
            idx = random.randrange(i, stop)
            self._order[i], self._order[idx] = self._order[idx], self._order[i]
            i += 1

    def __repr__(self) -> str:
        ret = "TaskPool(\n"
        for i, task in enumerate(self._tasks):
            ret += "{:>4}.  ".format(i) + repr(task) + "\n"
        ret += ")"
        return ret

    def finished(self):
        return len(self) == (self.num_failed() + self.num_success())

    def num_success(self):
        ret = 0
        for task in self:
            if task.status == Status.SUCCESS:
                ret += 1
        return ret

    def num_failed(self):
        ret = 0
        for task in self:
            if task.status == Status.FAILED:
                ret += 1
        return ret
