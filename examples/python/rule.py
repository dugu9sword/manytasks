import re
import numpy as np

def extract(text: list):
    scores = []
    max_epoch = None
    for line in text:
        if "valid on 'valid' subset" in line:
            found = re.search(r"accuracy ([\d\.]+)", line)
            scores.append(float(found.group(1)))
    if len(scores) > 1:
        return {"max_score": max(scores), "max_epoch": np.argmax(scores)}
    else:
        return {"max_score": None, "max_epoch": None}