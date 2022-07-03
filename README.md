# Manytasks

A lightweight tool for deploying many tasks automatically, without any modification to your code.

- [Manytasks](#manytasks)
  - [Installation](#installation)
  - [Quick Example](#quick-example)
  - [Sample Configuration](#sample-configuration)
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
      "--a", [50, 100],
      "-b", "$<range(10)>",   # "$<PYTHON SCRIPTS>" produces a list
      "--name", "a_${--a}"    # "${key}" refers to the value of an arg
    ],
    # more disjoint configurations
    "==more==": [
      [ "--c1", 1 ],                  # case 1
      [ "--c1", 2, "--c2", [3, 4] ],  # case 2
    ]
  }
}
```

which yields:
```bash
python some.py arg0 --a 50 --b 0 --name a_50 --c1 1
python some.py arg0 --a 50 --b 0 --name a_50 --c1 2 --c2 3
python some.py arg0 --a 50 --b 0 --name a_50 --c1 2 --c2 4

python some.py arg0 --a 50 --b 1 --name a_50 --c1 1
python some.py arg0 --a 50 --b 1 --name a_50 --c1 2 --c2 3
python some.py arg0 --a 50 --b 1 --name a_50 --c1 2 --c2 4
...
```

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


<!-- 
## Publications Using this Tool

*I'd like to claim that it is very STABLE 😊 and SUITABLE 👍 for research, it will make your skin smoother!*

- **Arxiv 2020**: *Chinese Named Entity Recognition Augmented with Lexicon Memory* (Accepted by **JCST 2022**). 
- **ACL 2020**: *Evaluating and Enhancing the Robustness of Neural Network-based Dependency Parsing Models with Adversarial Examples*. 
- **ACL 2021**: *Defense against Synonym Substitution-based Adversarial Attacks via Dirichlet Neighborhood Ensemble*.
- **WMT 2021**: *The Volctrans GLAT System: Non-autoregressive Translation Meets WMT21*.
- **EMNLP 2021**: *On the Transferability of Adversarial Attacks against Neural NLP Models*. 
- **EMNLP 2021**: *Searching for an Effiective Defender: Benchmarking Defense against Adversarial Word Substitution*. 
- **ACL 2022**: *Towards Adversarially Robust Text Classifiers by Learning to Reweight Clean Examples*. 
-->
