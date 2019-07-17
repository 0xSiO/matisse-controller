import types
from functools import wraps

from PyQt5.QtCore import pyqtSlot


# Inspired by this StackOverflow question:
# https://stackoverflow.com/questions/18740884/preventing-pyqt-to-silence-exceptions-occurring-in-slots
def handled_function(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            function(*args, **kwargs)
        except Exception:
            args[0].error_dialog()

    return wrapper


def handled_slot(*args):
    if len(args) == 0 or isinstance(args[0], types.FunctionType):
        args = []

    @pyqtSlot(*args)
    def slot_wrapper(func):
        return handled_function(func)

    return slot_wrapper
