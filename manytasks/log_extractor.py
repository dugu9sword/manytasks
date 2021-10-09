import os
import re
from typing import Callable, Dict, Iterable, List

import numpy as np
from tabulate import tabulate

from manytasks.defs import TaskPool


# Predefined filters
def include_filter(key):
    def _check(line):
        return key in line

    return _check


def exclude_filter(key):
    def _check(line):
        return key not in line

    return _check


def startswith_filter(key):
    def _check(line):
        return line.startswith(key)

    return _check


FILTERS = {
    "include": include_filter,
    "exclude": exclude_filter,
    "startswith": startswith_filter
}

# Predefined patterns
PATTERNS = {
    "INT": r"([-]*\d+)",
    "FLOAT": r"([-]*\d+\.\d+)",
    "BEFORE_COMMA": r"([^,]+),"
}

# Predefined reduction functions
REDUCE_FNS = {"max": max, "min": min, "sum": sum, "last": lambda x: x[-1]}


def extract(lines: Iterable,
            filters: List[Callable] = [],
            patterns: Dict[str, Callable] = {},
            reduce_fns: Dict[str, Callable] = {}):
    """
        Only lines which contains *all keys* in the patterns will be considered.

        Input:
            lines:     an iterable containing many strings
            filters:   a list of filters which removes useless lines
            patterns:
                { key1: pattern extractor 1, key2: pattern extractor 2, ... }
            reduce_fns:
                { key1: reduce function 1, key2: reduce function 2, ... }
                
        Returns:
                { key1: extracted values 1,  key2: extracted values 2, ... }
    """
    ret = {}
    for k in patterns:
        ret[k] = []

    for line in lines:
        skip_this_line = False
        for check in filters:
            if not check(line):
                skip_this_line = True
                continue
        if skip_this_line:
            continue
        found_num = 0
        line_result = {}
        for k, pattern in patterns.items():
            found = re.search(pattern, line)
            if found:
                found_num += 1
                line_result[k] = float(found.group(1))
            else:
                break
        if found_num == len(patterns):
            for k in ret:
                ret[k].append(line_result[k])
    if len(reduce_fns) != 0:
        for k in ret:
            if len(ret[k]) == 0:
                ret[k] = np.nan
            else:
                ret[k] = reduce_fns[k](ret[k])
    return ret


def show(opt, taskpool: TaskPool, regex_rule):
    table = []
    header = ["idx", "cmd"]
    for idx, task in enumerate(taskpool):
        task_log = "{}/task-{}.txt".format(opt.log_path, idx)
        if os.path.exists(task_log):
            text = open(task_log).readlines()
            extracted = {}
            for k, v in regex_rule.items():
                # set filters
                filters = []
                if "filter" in v:
                    for fk, fv in v["filter"].items():
                        filters.append(FILTERS[fk](fv))

                # set pattern
                pattern = v["pattern"]
                for pk in PATTERNS:
                    if "<{}>".format(pk) in pattern:
                        pattern = pattern.replace("<{}>".format(pk),
                                                  PATTERNS[pk])

                # set reduction function
                reduce_fn = REDUCE_FNS[v["reduce"]]

                result = extract(text,
                                 filters=filters,
                                 patterns={k: pattern},
                                 reduce_fns={k: reduce_fn})

                extracted[k] = result[k]

            table.append([idx, task.to_finalized_cmd(), *extracted.values()])
    header.extend(list(regex_rule.keys()))
    result = tabulate(table, headers=header, floatfmt=".4f")
    print(result)
    f = open("{}/result.txt".format(opt.log_path), "w")
    print(result, file=f)
