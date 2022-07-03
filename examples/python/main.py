import time
import random
from argparse import ArgumentParser
from math import log10


parser = ArgumentParser()
parser.add_argument(dest="data", action='store')
parser.add_argument('--arch', dest='arch', action='store')
parser.add_argument('--layer', dest='layer', type=int, action='store')
parser.add_argument('--opt', dest='opt', action='store')
parser.add_argument('--lr', dest='lr', type=float, action='store')
parser.add_argument('--decay', dest='decay', default=1e-2, type=float, action='store')
parser.add_argument('--fp16', dest='fp16', default=False, type=bool, action='store_true')
parser.add_argument('--fix-embedding', dest='fix_embeeding', default=False, type=bool, action='store_true')

args = parser.parse_args()

print(args)


"""
predefine the expected result
"""
# arch = transformer, layer = 12 is the best!
if args.arch == "transformer":
    if   1 <= args.layer <= 4:     bleu = 21.0
    elif 5 <= args.layer <= 8:     bleu = 25.0
    elif 9 <= args.layer <= 12:    bleu = 26.0
elif args.arch == "convs2s":
    if   1 <= args.layer <= 4:     bleu = 20.5
    elif 5 <= args.layer <= 8:     bleu = 24.5
    elif 9 <= args.layer <= 12:    bleu = 25.5
elif args.arch == "lstm":
    if   args.layer in [1]:        bleu = 24.0
    elif args.layer in [2, 3]:     bleu = 25.0
    elif args.layer in [4, 5]:     bleu = 23.0
    else:                          bleu = 21.0
elif args.arch == "rnn":
    bleu = 20.0
# opt = adam is always the best!
bleu = bleu + {
    "adam":    -0.0,
    "sgd":     -2.0,
    "adagrad": -1.0
}[args.opt]
# lr = 5e-4 is the best!
bleu -= log10(max(args.lr / 5e-4, 5e-4 / args.lr))
# decay = 1e-2 is the best!
bleu -= log10(max(args.decay / 1e-2, 1e-2 / args.decay))


# print("cuda device is {}".format(os.environ["CUDA_VISIBLE_DEVICES"]))

if random.randint(1, 100) < 20:
    print("Exception")
    raise Exception("ERROR")


epochs = 30
batches = 30

def get_bleu(epoch):
    ratio = (epoch + 1) / epochs
    factor = 2 / (1 + 2.718 ** -(10 * ratio)) - 1 + random.uniform(-0.01, 0.01)
    return factor * bleu

def loss(epoch):
    return 1 - get_bleu(epoch) / 30.0

for i in range(epochs):
    for j in range(batches):
        print(f"| train | epoch {i} batch {j} | training loss {loss(i)}")
    print(f"| valid | epoch {i} | valid on 'valid' subset | bleu {get_bleu(i)} loss {loss(i)} | cost 10 seconds")
time.sleep(3)
