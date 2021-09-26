from argparse import ArgumentParser
import time

parser = ArgumentParser()
parser.add_argument(dest="data", action='store')
parser.add_argument('--arch', dest='arch', action='store')
parser.add_argument('--layer', dest='layer', action='store')
parser.add_argument('--name', dest='name', action='store')

parsed_args = parser.parse_args()

print(parsed_args)
time.sleep(10)