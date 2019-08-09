"""Utility functions and decorators for use in the GUI."""

import traceback
import types
from concurrent.futures import Future
from functools import wraps

from PyQt5.QtCore import pyqtSlot


def handled_function(function):
    """
    Wraps a given function in a try-except clause, calling `error_dialog` on the 'self' parameter to the function.
    Exception info can be accessed from the other function using `sys.exc_info()`.

    Inspired by this StackOverflow question:
    https://stackoverflow.com/questions/18740884/preventing-pyqt-to-silence-exceptions-occurring-in-slots

    Parameters
    ----------
    function
        the function you want to handle errors for

    Returns
    -------
    function
        a wrapper that calls `error_dialog` on the instance running the wrapped function
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
    Exactly like `handled_function`, but for a PyQt slot.
    Type arguments to the slot are specified just like in pyqtSlot.

    Parameters
    ----------
    *args
        type arguments to give to pyqtSlot

    Returns
    -------
    function
        a `handled_function` that is also a pyqtSlot
    """
    if len(args) == 0 or isinstance(args[0], types.FunctionType):
        args = []

    @pyqtSlot(*args)
    def slot_wrapper(func):
        return handled_function(func)

    return slot_wrapper


def raise_error_from_future(future: Future):
    """
    If you'd lke to log errors that occur in thread pools, call `add_done_callback` on the future returned from
    `ThreadPoolExecutor.submit` and pass in this function.
    """
    async_task_error: Exception = future.exception()
    if async_task_error:
        # Using the error_dialog method here seems to just hang the application forever.
        # Workaround: log error, make a noise, alert the user, and hope for the best
        message = f"An error occurred while running an asynchronous task: <pre>{traceback.format_exc()}</pre>"
        print(red_text(message))


# Text formatting utilities

def red_text(text):
    return f"<span style='color:red'>{text}</span>"


def orange_text(text):
    return f"<span style='color:orange'>{text}</span>"


def green_text(text):
    return f"<span style='color:green'>{text}</span>"
