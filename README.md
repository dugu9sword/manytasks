# Manytasks

A lightweight tool for deploying many tasks automatically, without any modification to your code.

- [Manytasks](#manytasks)
  - [Installation](#installation)
  - [Quick Example](#quick-example)
  - [Sample Configuration](#sample-configuration)
    - [Syntax Sugar](#syntax-sugar)
  - [Design Philosophy](#design-philosophy)
  - [Analysis](#analysis)
  - [History](#history)


## Installation

I **recommend** you install from github to get the newest features:

`pip install git+https://github.com/dugu9sword/manytasks.git` 

You can also install the package (**maybe outdated**) from pypi:

`pip install manytasks [not recommended]` 


## Quick Example

```
cd examples/python

# configuration is stored in tasks.json
manytasks run tasks
```

All running logs are stored in `tasks.logs`. 

- The running log of the manytasks is written into `task.logs/status.txt` 

- The IO stream of tasks (e.g. `print()`, `Exception`, `Error`, ...) are redirected to `task.logs/task-[index].txt`.


## Sample Configuration

For more complex cases, see `ADVANCED_CASES.md`.

```python
{
  "executor": "python some.py",    
  "cuda": [4, 5, 6, 7],
  "concurrency": 4,           # num of tasks to run in parallel
  "cuda_per_task": 1,
  "configs": {
    # basic configurations
    "==base==": [          
      "arg0",
      "--a", [50, 100],       # `--a` takes value from [50, 100]
      "--name", "a_${a}"      # "${a}" refers to the value of `--a`
    ],
    # more disjoint configurations
    "==more==": [
      [ "--c1", [1, 2] ],            # [1, 2]
      [ "--c2", "$<x|y>.$<1:4>" ],   # [x.1, x.2, x.3, y.1, y.2, y.3]
    ]
  }
}
```

which yields:
```bash
---  ----  ---  ------  ----  ----
idx  __1   --a  --name  --c1  --c2
0    arg0  50   a_50    1     -
1    arg0  50   a_50    2     -
2    arg0  100  a_100   1     -
3    arg0  100  a_100   2     -
4    arg0  50   a_50    -     x.1
5    arg0  50   a_50    -     x.2
6    arg0  50   a_50    -     x.3
7    arg0  50   a_50    -     y.1
8    arg0  50   a_50    -     y.2
9    arg0  50   a_50    -     y.3
10   arg0  100  a_100   -     x.1
11   arg0  100  a_100   -     x.2
12   arg0  100  a_100   -     x.3
13   arg0  100  a_100   -     y.1
14   arg0  100  a_100   -     y.2
15   arg0  100  a_100   -     y.3
---  ----  ---  ------  ----  ----
```

### Syntax Sugar

The syntax sugar makes the enumeration of arguments more easier.

| Type                     | Example Input                | Example Output                             |
| ------------------------ | ---------------------------- | ------------------------------------------ |
| **list**                 | `$<1:6>`                     | `[1, 2, 3, 4, 5]`                          |
| **list** (with step)     | `$<1:6:2>`                   | `[1, 3, 5]`                                |
| **list** (with zero-pad) | `$<1:6:2;3>`                | `[001, 003, 005]`                          |
| **files**                | `$<files:/home/*.py>`       | `[/home/foo.py, /home/bar.py, ...]`                     |
| **files** (without path) | `$<files:/home/*.py;nameonly>`  | `[foo.py, bar.py, ...]`                     |
| **lines**                | `$<lines:urls.txt>`         | `[baidu.com, google.com, ...]`              |
| **set**          | `$<a\|b\|c>`               | `[a, b, c]`                                |
| **composition** | `x_$<1:3;3>.txt` | `[x_001.txt, x_002.txt]` |
| **composition** (more) | `logs/$<a\|b>.$<1:3>`         | `[logs/a.1, logs/a.2, logs/b.1, logs/b.2]` |





## Design Philosophy

**Q**: Why not use other open-source tools for hyper-parameter tuning, such as `optuna`, `hydra`, `wandb`?

**A**: The first time I developed this tool is 2019-1-1, when most of those tools (except `optuna`) were **not born** yet. What's more, 

- These tools are **heavy**, which means:
    - You need to modify your code (add several lines of `import xxx; xxx.foo(); xxx.bar();`) to integrate their functionalities.
    - You may have to replace your `print(...)` or `log(...)` function with theirs, sometimes your results may be logged to their server. 
    - These tools are highly binded with `python`, which means they may fail if your code is written in `perl` (such as `mosetokenizer` in machine translation), `bash` (such as your code for preprocessing), etc.
- `manytasks` is a lightweight tool which helps you deploy many tasks **without any modification** to your code, all logs will be saved in your machine.

**Q**:When should you use other open-source tools for hyper-parameter tuning, such as `optuna`, `hydra`, `wandb`?

**A**: For complex cases when you would like to enjoy their power of hyper-parameter tuning.

## Analysis

See `Analysis.md`.

## History

See `History.md`.
