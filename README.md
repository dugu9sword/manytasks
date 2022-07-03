# Manytasks

A lightweight tool for deploying many tasks automatically, without any modification to your code.

* [Manytasks](#manytasks)
   <!-- * [Publications Using this Tool](#publications-using-this-tool) -->
   * [Installation](#installation)
   * [Quick Example](#quick-example)
   * [Sample Configuration](#sample-configuration)
   * [Design Philosophy](#design-philosophy)
   * [Advanced Usage](#advanced-usage)
   * [History](#history)


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

For more details, see `examples/advanced_configs`.

```python
{
  # any runnable program, python/perl/bash/java, etc. 
  "executor": "python some.py",    
  # When cuda is set to -1/[]/[-1], ManyTasks will not set 
  # the environment variable CUDA_VISIBLE_DEVICES. 
  "cuda": [0, 1],
  # How many processes will be run in parallel?
  #     - "#CPU" (number of CPUs)
  #     - "#CUDA" (number of CUDA devices)
  #     - an integer  
  "concurrency": 2,
  "configs": {
    # basic configurations
    "==base==": [          
      # an arg without a key
      "arg0",
      # a list of values
      "--a", [50, 100],
      # use "...$<PYTHON SCRIPTS>..." to produce a list
      "-b", "$<range(10)>",
      # use "...${key}..." to refer to an arg
      "--name", "a_${--a}_b_${-b}"
    ],
    # more disjoint configurations
    "==more==": [
      # case 1
      [
        "--c1", 1
      ],
      # case 2
      [
        "--c1", 2
        "--c2", [3, 4]
      ],
    ]
  }
}
```

which yields:
```bash
python some.py arg0 --a 50 --b 0 --name a_50_b_0 --c1 1
python some.py arg0 --a 50 --b 0 --name a_50_b_0 --c1 2 --c2 3
python some.py arg0 --a 50 --b 0 --name a_50_b_0 --c1 2 --c2 4

python some.py arg0 --a 50 --b 1 --name a_50_b_0 --c1 1
python some.py arg0 --a 50 --b 1 --name a_50_b_0 --c1 2 --c2 3
python some.py arg0 --a 50 --b 1 --name a_50_b_0 --c1 2 --c2 4
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

## Advanced Usage

See `Advance Usage.md`.

## History

See `History.md`.