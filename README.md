# Alchemist - 炼丹师

*2019.1.1, the first version comes!*

A toy tool for deep learning, which helps explore different net configurations.

- [x] Enumerate different configurations
- [x] Specify which GPU card to use
- [x] Specify the number of processes
- [x] Web UI support
- [x] Show the last 100 lines of logs
- [x] Show the GPU overload

## Clone & Install

`git clone https://github.com/dugu9sword/alchemist.git`

`python setup.py install`

## Usage

- Configuration

A sample task configuration is stored in `sample_task.json`.

- Running

`alchemist --task=sample_task.json`

You can view the running status via "http://127.0.0.1:5000" (**the port number may differs**, you can get the port number from the command line)

![sample](sample.png)

- Results

All running logs are stored in `sample_task.json.logs`. You can click the item in the list to view the last 100 lines of the log.

The running log of the alchemist is written into `alchemist.log` 

The IO stream of tasks (e.g. `print()`, `Exception`, `Error`, ...) are redirected to `task-[index].txt`.

## Sample Configuration

```
{
  "executor": "python3",   # python interpreter
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
