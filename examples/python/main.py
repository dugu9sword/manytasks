import time
import random
from argparse import ArgumentParser
from math import log


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

if random.randint(1, 100) < 20:
    print("Exception")
    raise Exception("ERROR")

epochs = 20
batches = 30

factor = random.random()
final_accu = random.uniform(0.8, 1.0)

def accu(epoch):
    min_accu = (epoch / epochs) ** factor
    max_accu = ((epoch + 1) / epochs) ** factor
    return random.uniform(min_accu, max_accu) * final_accu

def loss(epoch):
    return 1 - accu(epoch)

for i in range(epochs):
    for j in range(batches):
        print(f"| train | epoch {i} batch {j} | training accuracy {accu(i)}")
    print(f"| valid | epoch {i} | valid on 'valid' subset | accuracy {accu(i)} loss {loss(i)} | cost 10 seconds")
    # time.sleep(1)
