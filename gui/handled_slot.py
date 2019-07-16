import types
from functools import wraps

from PyQt5 import QtCore


# Inspired by this StackOverflow question:
# https://stackoverflow.com/questions/18740884/preventing-pyqt-to-silence-exceptions-occurring-in-slots
def HandledSlot(*args):
    if len(args) == 0 or isinstance(args[0], types.FunctionType):
        args = []

    @QtCore.pyqtSlot(*args)
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                function(*args)
            except Exception:
                args[0].error_dialog()

        return wrapper

    return decorator
