import json


def load_task(path="task.json"):
    task = json.load(fp=open(path))
    executor = task["executor"]
    runnable = task["runnable"]
    cuda = task["cuda"]
    concurrency = task["concurrency"]
    base_conf = task["configs"]["==base=="]
    more_confs = task["configs"]["==more=="]
    _base_conf = []
    for ele in base_conf:
        if isinstance(base_conf[ele], list):
            _base_conf.append((ele, base_conf[ele]))
        else:
            _base_conf.append((ele, [base_conf[ele]]))
    _more_confs = []
    for more_conf in more_confs:
        _more_conf = []
        for ele in more_conf:
            if isinstance(more_conf[ele], list):
                _more_conf.append((ele, more_conf[ele]))
            else:
                _more_conf.append((ele, [more_conf[ele]]))
        _more_confs.append(_more_conf)
    parsed_confs = []
    if len(_more_confs) == 0:
        parsed_confs.append(_base_conf)
    for _more_conf in _more_confs:
        parsed_confs.append(_base_conf + _more_conf)
    return executor, runnable, cuda, concurrency, parsed_confs
