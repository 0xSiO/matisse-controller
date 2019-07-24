import json
import operator
from functools import reduce

CONFIGURATION = {}


def get(name):
    keys = name.split('.')
    return reduce(operator.getitem, keys, CONFIGURATION)


def load():
    with open('config.json', 'r') as config_file:
        global CONFIGURATION
        CONFIGURATION = json.load(config_file)


def save():
    with open('config.json', 'w') as config_file:
        json.dump(CONFIGURATION, config_file, indent=4)
