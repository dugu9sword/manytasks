from typing import List

# Definition
class Arg:
    def __init__(self, key, value) -> None:
        self.key: str = key
        self.value = value


class Task:
    def __init__(self, args) -> None:
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

    def __contains__(self, key):
        return key in self.keys

    def __setitem__(self, key, value):
        self.args[self.keys.index(key)].value = value

    def __getitem__(self, key):
        return self.args[self.keys.index(key)].value

    def __iter__(self):
        return iter(self.args)

    def __repr__(self):
        return f"Task(Arg={self.to_finalized_args()}, Status={self.status})"

    def to_callable_args(self):
        """
            Return: ["arg0", "--key1", "arg1", "--key2", "arg2"]
        """
        buff = []
        for arg in self.args:
            if arg.key.startswith("__"):
                buff.append(arg.value)
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
        return executor + " " + self.to_finalized_args()

class Mode:
    NORMAL   = "NORMAL"
    OVERRIDE = "OVERRIDE"
    RESUME   = "RESUME"

class Status:
    SUCCESS  = "SUCCESS"
    FAILED   = "FAILED"
    PENDING  = "PENDING"
    RUNNING  = "RUNNING"


# Variables
mode = "<mode>"
config_name = "<config>"
log_path = "<path>"
executor = "<python>"
cuda = [0, 1, 2]
concurrency = -1
tasks: List[Task] = []
