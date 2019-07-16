from functools import wraps


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
