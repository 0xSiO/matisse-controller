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
                'range_small': 200,  # TODO: Check the 'small' scan ranges
                'step': 4
            },
            'thin_etalon': {
                'range': 2000,
                'range_small': 1000,
                'step': 10,
                'nudge': 50  # TODO: Confirm this parameter is ok to use, flank seems to default to 'left'?
            },
            'refcell': {
                'rising_speed': 0.01,  # TODO: Confirm sensible defaults for all rising/falling speeds
                'falling_speed': 0.01
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
        'stabilization': {
            'rising_speed': 0.01,
            'falling_speed': 0.01,
            'delay': 0.5,
            'tolerance': 0.0005
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


def get(name: str):
    """Fetch the global configuration value represented by the specified name."""
    keys = name.split('.')
    return reduce(operator.getitem, keys, CONFIGURATION)


def set(name: str, value):
    """Set the global configuration value represented by the specified name."""
    keys = name.split('.')
    cfg = CONFIGURATION
    for key in keys[:-1]:
        cfg = cfg.get(key)
    cfg[keys[-1]] = value


def load(filename: str):
    """Load configuration data from a file into the global configuration dictionary."""
    with open(filename, 'r') as config_file:
        global CONFIGURATION
        CONFIGURATION = json.load(config_file)


def save():
    """Save the global configuration data to a config.json file."""
    with open('config.json', 'w') as config_file:
        json.dump(CONFIGURATION, config_file, indent=4)


def restore_defaults():
    """Overwrite the global configuration with the defaults, specified by configuration.DEFAULTS."""
    global CONFIGURATION
    CONFIGURATION = copy.deepcopy(DEFAULTS)


if path.exists('config.json'):
    load('config.json')
else:
    restore_defaults()
