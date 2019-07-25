import copy
import json
import operator
from functools import reduce
from os import path

CONFIGURATION = {}
DEFAULTS = {
    'matisse': {
        'device_id': 'USB0::0x17E7::0x0102::07-40-01::INSTR',
        'scanning': {
            'birefringent_filter': {
                'range': 400,
                'range_small': 200,
                'step': 4
            },
            'thin_etalon': {
                'range': 2000,
                'range_small': 1000,
                'step': 10,
                'nudge': 50
            },
            'wavelength_drift': {
                'large': 0.4,
                'medium': 0.2,
                'small': 0.02
            },
        },
        'locking': {
            'timeout': 7.0
        },
        'correction': {
            'piezo_etalon_pos': 0.0,
            'slow_piezo_pos': 0.35,
            'refcell_pos': 0.35
        }
    },
    'wavemeter': {
        'port': 'COM5',
        'precision': 3
    },
    'gui': {}
}


def get(name):
    keys = name.split('.')
    return reduce(operator.getitem, keys, CONFIGURATION)


def set(name, value):
    keys = name.split('.')
    cfg = CONFIGURATION
    for key in keys[:-1]:
        cfg = cfg.get(key)
    cfg[keys[-1]] = value


def load(filename):
    with open(filename, 'r') as config_file:
        global CONFIGURATION
        CONFIGURATION = json.load(config_file)


def save():
    with open('config.json', 'w') as config_file:
        json.dump(CONFIGURATION, config_file, indent=4)


def restore_defaults():
    global CONFIGURATION
    CONFIGURATION = copy.deepcopy(DEFAULTS)


if path.exists('config.json'):
    load('config.json')
else:
    restore_defaults()
