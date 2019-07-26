import types
from functools import wraps

from PyQt5.QtCore import pyqtSlot


# Inspired by this StackOverflow question:
# https://stackoverflow.com/questions/18740884/preventing-pyqt-to-silence-exceptions-occurring-in-slots
def handled_function(function):
    """
    Wraps a given function in a try-except clause, calling error_dialog on the 'self' parameter to the function.
    Exception info can be accessed from the other function using sys.exc_info().

    :param function: the function you want to handle errors for
    :return: a wrapper that calls error_dialog on the instance running the wrapped function
    """

    @wraps(function)
    def handled_function_wrapper(*args, **kwargs):
        try:
            function(*args, **kwargs)
        except Exception:
            args[0].error_dialog()

    return handled_function_wrapper


def handled_slot(*args):
    """
    Exactly like handled_function, but for a PyQt slot. Type arguments to the slot are specified just like in pyqtSlot.

    :param args: type arguments to give to pyqtSlot
    :return: a handled_function that is also a pyqtSlot
    """
    if len(args) == 0 or isinstance(args[0], types.FunctionType):
        args = []

    @pyqtSlot(*args)
    def slot_wrapper(func):
        return handled_function(func)

    return slot_wrapper


# Text formatting utilities

def red_text(text):
    return f"<span style='color:red'>{text}</span>"


def orange_text(text):
    return f"<span style='color:orange'>{text}</span>"


def green_text(text):
    return f"<span style='color:green'>{text}</span>"
