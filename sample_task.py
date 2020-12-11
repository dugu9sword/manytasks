import time
import random
import os
import argparse


class ProgramArgs(argparse.Namespace):
    def __init__(self):
        super(ProgramArgs, self).__init__()
        self.a = 10
        self.b = 120


parser = argparse.ArgumentParser()
nsp = ProgramArgs()
for key, value in nsp.__dict__.items():
    parser.add_argument('--{}'.format(key),
                        action='store',
                        default=value,
                        type=type(value),
                        dest=str(key))
config = parser.parse_args(namespace=nsp)  # type: ProgramArgs

print("arg a is {}, b is {}".format(config.a, config.b))
# print("cuda device is {}".format(os.environ["CUDA_VISIBLE_DEVICES"]))

sec = random.randint(1, 6)
if sec < 3:
    print("Exception")
    raise Exception("ERROR")
print("sleep for {} seconds".format(sec))
time.sleep(sec)
