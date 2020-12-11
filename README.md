# Manytasks

A tool for deploying many tasks automatically.

## Clone & Install

The simplest way to install the package is:

`pip install manytasks`

or you can install from github to get the newest features:

`pip install git+https://github.com/dugu9sword/manytasks.git`


## Usage

- Configuration

A sample task configuration is stored in `sample_task.hjson`.

- Running

`manytasks --task=sample_task`

You can view the running status via "http://127.0.0.1:5000" (**the port number may differs**, you can get the port number from the command line)

![sample](sample.png)

- Results

All running logs are stored in `sample_task.logs`. You can click the item in the list to view the last 100 lines of the log.

The running log of the manytasks is written into `manytasks.txt` 

The IO stream of tasks (e.g. `print()`, `Exception`, `Error`, ...) are redirected to `task-[index].txt`.

## Sample Configuration

```
{
  "executor": "python",   # python interpreter
  "runnable": "some.py",   # the runnable file
  "cuda": [0, 1],          # [-1 if not using cuda] cuda index to use
  "concurrency": 2,        # number of multi-processes 
  "configs": {
    "==base==": {          # basic configurations
      "--word-emb": [50, 100]
    },
    "==more==": [          # [can be empty] some different configurations
      {                    # supposing using lstm as the representation layer
        "--use-lstm": True,
        "--lstm-hidden": 200
        ...
      },
      {                    # supposing using transformer as the representation layer
        "--use-transformer": True,
        "--num-head": 8,
        "--num-layer": 6,
        ...
      }
    ]
  }
}
```

## History
**2020.12.12**, Big changes! I will resubmit my paper to ACL 2021 recently. Before that, I want to publish this repo to `pypi` so that you can install it by `pip install ...` directly. I rename `manytasks` to `manytasks` to make the name of the tool easier to recognize, and change the description *A toy tool for deep learning, which helps explore different net configurations.* to *A tool for deploying many tasks automatically.*

- [x] Colorize the CLI tools
- [x] Disable the web UI by default

**2019.12.11**, About one year later, after submitting my ACL 2020 paper, I add some new features to the tool. Good luck~

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
