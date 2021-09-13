import re
from collections import OrderedDict
from typing import List
import numpy as np

from tabulate import tabulate


def show(log_path, extract_fn):
    tasks = {}
    status = open("{}/status.txt".format(log_path)).readlines()
    for line in status:
        found = re.search(r"TASK (\d+)/(\d+).*: (.*)", line)
        if found:
            idx = int(found.group(1))
            cmd = found.group(3)
            tasks[idx] = cmd
    tasks = OrderedDict(sorted(tasks.items()))
    table = []
    header = ["idx", "cmd"]
    ret = None
    for idx in tasks:
        ret = extract_fn(open("{}/task-{}.txt".format(log_path, idx)).readlines())
        for key in ret:
            if ret[key] is None:
                ret[key] = np.nan
        table.append([idx, tasks[idx], *ret.values()])
    if ret:
        header.extend(list(ret.keys()))
        table.insert(0, header)
    result = tabulate(table, floatfmt=".3f")
    f = open("{}/result.txt".format(log_path), "w")
    print(result)
    print(result, file=f)


def extract_last_line(text: List[str]):
    return {"last_line": text[-1].strip()}


def extract_by_regex(regex_dict, text: List[str]):
    ret = {}
    for k, v in regex_dict.items():
        data = []
        for line in text:
            if "include" in v and v["include"] not in line:
                continue
            found = re.search(v["regex"], line)
            if found:
                data.append(float(found.group(1)))
        reduce_fn = {
            "max": max,
            "min": min,
            "sum": sum
        }[v['reduce']]
        if len(data) == 0:
            ret[k] = None
        else:
            ret[k] = reduce_fn(data)   
    return ret
