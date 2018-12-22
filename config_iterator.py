from typing import NamedTuple, List

Arg = NamedTuple("Arg", [("key", str),
                         ("value", object)])
ArgGroup = List[Arg]
ArgGroupList = List[ArgGroup]


def next_config_idx(configs, config_idx):
    idx = -1
    ret = list(config_idx)
    while True:
        if idx < -len(config_idx):
            return None
        ret[idx] += 1
        if ret[idx] < len(configs[idx][1]):
            return ret
        else:
            ret[idx] = 0
            idx -= 1


def gen_arg_list(configs):
    tmp_configs = []
    for i in range(len(configs)):
        if not isinstance(configs[i][1], list):
            tmp_configs.append((configs[i][0], [configs[i][1]]))
        else:
            tmp_configs.append((configs[i][0], configs[i][1]))
    configs = tmp_configs

    arg_group_list: ArgGroupList = []
    config_idx = [0 for _ in range(len(configs))]
    while config_idx is not None:
        args: ArgGroup = []
        for i in range(len(configs)):
            args.append(Arg(key=configs[i][0],
                            value=configs[i][1][config_idx[i]]))
        arg_group_list.append(args)
        config_idx = next_config_idx(configs, config_idx)
    return arg_group_list


def main():
    config = [
        ("seed", [314159, 26535, 897932]),
        ("future_day", 4),
        ("hidden_size", [30]),
        ("cell_type", ["GRU"]),
    ]
    print(gen_arg_list(config))


if __name__ == '__main__':
    main()
