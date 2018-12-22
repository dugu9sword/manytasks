import time
import random
import os

print(os.environ["CUDA_VISIBLE_DEVICES"])

sec = random.randint(3, 10)
print("A task to sleep for {} seconds".format(sec))
time.sleep(sec)

