# Manytasks

A tool for deploying many tasks automatically.

## Publications Using this Tool

- **Arxiv 2020**: *Chinese Named Entity Recognition Augmented with Lexicon Memory*. 
- **ACL 2020**: *Evaluating and Enhancing the Robustness of Neural Network-based Dependency Parsing Models with Adversarial Examples*. 
- **ACL 2021**: *Defense against Synonym Substitution-based Adversarial Attacks via Dirichlet Neighborhood Ensemble*.
- **WMT 2021**: *The Volctrans Parallel Machine Translation System for WMT21 German-English News Translation Task*.
- **EMNLP 2021**: *On the Transferability of Adversarial Attacks against Neural NLP Models*. 
- **EMNLP 2021**: *Searching for an Effiective Defender: Benchmarking Defense against Adversarial Word Substitution*. 

## Installation

I **recommend** you install from github to get the newest features:

`pip install git+https://github.com/dugu9sword/manytasks.git` 

You can also install the package (**maybe outdated**) from pypi:

`pip install manytasks [not recommended]` 


## Quick Example

```
cd examples/python

# configuration is stored in task.json
manytasks run task
```

All running logs are stored in `task.logs`. 

- The running log of the manytasks is written into `task.logs/status.txt` 

- The IO stream of tasks (e.g. `print()`, `Exception`, `Error`, ...) are redirected to `task.logs/task-[index].txt`.


## Sample Configuration

```
{
  "executor": "python some.py",    # runnable
  "cuda": [0, 1],                  # [-1 if not using cuda] cuda index to use
  "concurrency": 2,                # number of multi-processes
  "configs": {
    "==base==": [                  # basic configurations
      "--word-emb", [50, 100],
      "--learning-rate", "{range(0.001, 0.1, 0.001)}"
    ],
    "==more==": []
  }
}
```

## Advanced Usage


- Result Extraction

You can extract results (`accuracy`, `F-1`, `BLEU`, etc. ) from generated logs by writing simple rules. 

Try: 

`manytasks show task --rule=rule.yaml`

You will get:

```
---  -----------------------------------------------------------------------------  ------------------  ----------------------
idx  cmd                                                                            accuracy            loss
0    python main.py wmt14 --arch lstm --layer 2 --opt adam --lr 1e-2 --decay 0.01   nan                 nan
1    python main.py wmt14 --arch lstm --layer 2 --opt adam --lr 1e-2 --decay 0.001  0.969389853637771   0.018800431068203283
2    python main.py wmt14 --arch lstm --layer 2 --opt adam --lr 1e-3 --decay 0.01   nan                 nan
3    python main.py wmt14 --arch lstm --layer 2 --opt adam --lr 1e-3 --decay 0.001  nan                 nan
4    python main.py wmt14 --arch lstm --layer 2 --opt adam --lr 5e-4 --decay 0.01   0.9953219531778092  0.0025735338086863013
5    python main.py wmt14 --arch lstm --layer 2 --opt adam --lr 5e-4 --decay 0.001  0.9738390095674021  0.002672132175549624
6    python main.py wmt14 --arch cnn --layer 2 --opt adam --lr 1e-2 --decay 0.01    nan                 nan
7    python main.py wmt14 --arch cnn --layer 2 --opt adam --lr 1e-2 --decay 0.001   0.9976834837298412  0.0038932645925157106
8    python main.py wmt14 --arch cnn --layer 2 --opt adam --lr 1e-3 --decay 0.01    0.9737320897655711  0.0295369931044418
9    python main.py wmt14 --arch cnn --layer 2 --opt adam --lr 1e-3 --decay 0.001   0.9727926577331226  0.03280128785619396
10   python main.py wmt14 --arch cnn --layer 2 --opt adam --lr 5e-4 --decay 0.01    0.9950810301325252  0.00028976052740525837
11   python main.py wmt14 --arch cnn --layer 2 --opt adam --lr 5e-4 --decay 0.001   0.966193556539577   0.010192030493943904
12   python main.py wmt14 --arch lstm --layer 2 --opt sgd --lr 1e-1                 nan                 nan
13   python main.py wmt14 --arch lstm --layer 2 --opt adagrad --lr 1e-1             0.9991008494755877  0.00862301177187852
14   python main.py wmt14 --arch cnn --layer 2 --opt sgd --lr 1e-1                  0.990682658916566   0.010620481443061158
15   python main.py wmt14 --arch cnn --layer 2 --opt adagrad --lr 1e-1              nan                 nan
---  -----------------------------------------------------------------------------  ------------------  ----------------------
```

You can even write a python function to extract the results.

`manytasks show task --rule=rule.py`

- Plotting Curves

See `examples/python/analyze_log.ipynb` for details.

<img src="sample_curve.png" alt="drawing"/>

- Factor Analsis

See `examples/python/analyze_log.ipynb` for details.

<!-- ![Factor Analysis](sample_analysis.png) -->

<img src="sample_factor.png" alt="drawing"/>


## History

**2021.9.13**, Small changes.
- [x] Add support for specifying an output directory
- [x] Add better support for log analysis.

**2021.6.20**, Big changes.
- [x] Deprecate support for WebUI.
- [x] Add support for resuming from the last running status.
- [x] Add support for factor analysis.

**2021.5.26**, Small changes.
- [x] Add support for yaml rule & Deprecate support for json rule (regex in json is not readable)

**2021.3.16**, Small changes.

- [x] Support for JSON rule.
- [x] Beautify the command line output.

**2021.2.18**, Big changes.

- [x] Support Non-key arguments
- [x] Support for setting latency between two tasks (sometimes task-2 may reuse the cached data generated by task-1, so it is a good idea to let task-2 wait for a few seconds) 
- [x] Remove the arg `runnable` and merge it into `executor`
- [x] Support for result extraction

**2020.12.12**, Big changes! I will submit my paper to ACL 2021 recently (accepted!). Before that, I want to publish this repo to `pypi` so that you can install it by `pip install ...` directly. I rename `alchemist` to `manytasks` to make the name of the tool easier to recognize, and change the description *A toy tool for deep learning, which helps explore different net configurations.* to *A tool for deploying many tasks automatically.*

- [x] Colorize the CLI tools
- [x] Disable the web UI by default
- [x] Support for configuration with python script
- [x] Support for init a config
- [x] Support for showing the results

**2019.12.11**, About one year later, after submitting my ACL 2020 paper (accepted!), I add some new features to the tool. Good luck~

- [x] Use `.hjson` (<https://hjson.org/>) instead of `.json` for configuration, since `.hjson` is more human-readable which allows comments and missing/trailing commas
- [x] Ask the user for overriding existing logs
- [x] Beautify the CLI tools

**2019.1.1**, First version comes out. I wrote the code to enable grid search for my ACL 2019 submission. Unfortunately it was rejected. :(

- [x] Enumerate different configurations
- [x] Specify which GPU card to use
- [x] Specify the number of processes
- [x] Web UI support
- [x] Show the last 100 lines of logs
- [x] Show the GPU overload
