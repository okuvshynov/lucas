import json
from copy import deepcopy

stats = {}

def bump(key, value=1):
    current = stats.get(key, 0)
    stats[key] = current + value

def dump():
    return deepcopy(stats)
