# Alchemist

A tool for deep learning, which helps explore different net configurations.

- Enumerate different configurations
- Specify which GPU card to use
- Specify the number of processes

## Usage

`python alchemist --task=sample_task.json`

See `sample_task.json` for more details.

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
