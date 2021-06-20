import time
import random
from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument(dest="data", action='store')
parser.add_argument('--arch', dest='arch', action='store')
parser.add_argument('--layer', dest='layer', action='store')
parser.add_argument('--opt', dest='opt', action='store')
parser.add_argument('--lr', dest='lr', action='store')
parser.add_argument('--decay', dest='lr', action='store')

parsed_args = parser.parse_args()

print(parsed_args)
# print("cuda device is {}".format(os.environ["CUDA_VISIBLE_DEVICES"]))

sec = random.randint(1, 6)
if sec < 3:
    print("Exception")
    raise Exception("ERROR")

for i in range(sec):
    for j in range(10):
        print(f"| train | epoch {i} batch {j} | training accuracy {random.random()}")
    print(f"| valid | epoch {i} | valid on 'valid' subset | accuracy {random.random()} loss {random.random()} | cost 10 seconds")
    time.sleep(1)
