import operator
from functools import reduce


class Configuration(dict):
    def get(self, name):
        keys = name.split('.')
        return reduce(operator.getitem, keys, self)

    def set(self, name, value):
        keys = name.split('.')
        self.get('.'.join(keys[:-1]))[keys[-1]] = value
