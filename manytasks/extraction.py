import os
import re
from typing import List

import numpy as np
from tabulate import tabulate

from manytasks.shared import TaskPool


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
    "INT":          r"([-]\d+)",
    "FLOAT":        r"([-]*\d+\.\d+)",
    "BEFORE_COMMA": r"([^,]+),"   
}


# Predefined reduction functions
REDUCE = {
    "max": max,
    "min": min,
    "sum": sum,
    "last": lambda x: x[-1]
}

def extract(lines, filters=[], patterns={}):
    """
        Input:
            lines:    an iterable containing many strings
            filters:  a list of filters which removes useless lines
            patterns: 
                { key1: pattern extractor 1, key2: pattern extractor 2, ... }
        Returns:
                { key1: extracted values 1,  key2: extracted values 2, ... }
    """
    ret = {}
    for k in patterns:
        ret[k] = []

    for line in lines:
        for check in filters:
            if not check(line):
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
    return ret

def extract_by_regex_rule(regex_rule, text: List[str]):
    ret = {}
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
                pattern = pattern.replace("<{}>".format(pk), PATTERNS[pk])
        
        result = extract(text, filters=filters, patterns={k: pattern})
        
        # set reduction function
        reduce_fn = REDUCE[v["reduce"]]
        if len(result[k]) == 0:
            ret[k] = np.nan
        else:
            ret[k] = reduce_fn(result[k])   
    return ret

def show(log_path, regex_rule):
    taskpool = TaskPool()
    table = []
    header = ["idx", "cmd"]
    ret = None
    for idx, task in enumerate(taskpool):
        task_log = "{}/task-{}.txt".format(log_path, idx)
        if os.path.exists(task_log):
            ret = extract_by_regex_rule(regex_rule, open(task_log).readlines())
            table.append([idx, task.to_finalized_cmd(), *ret.values()])
    if ret:
        header.extend(list(ret.keys()))
        table.insert(0, header)
    result = tabulate(table, floatfmt=".3f")
    f = open("{}/result.txt".format(log_path), "w")
    print(result)
    print(result, file=f)
