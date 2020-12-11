import time
import random
from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument('--a', dest='a', action='store')
parser.add_argument('--b', dest='b', action='store')
parser.add_argument('--c', dest='c', action='store')
parsed_args = parser.parse_args()

print(parsed_args)
# print("cuda device is {}".format(os.environ["CUDA_VISIBLE_DEVICES"]))

sec = random.randint(1, 6)
if sec < 3:
    print("Exception")
    raise Exception("ERROR")
print("sleep for {} seconds".format(sec))
time.sleep(sec)
