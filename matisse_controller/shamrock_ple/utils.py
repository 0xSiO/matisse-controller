import os
from ctypes import WinDLL, windll
from os import path


def load_lib(name: str) -> WinDLL:
    """
    Load the specified dynamic link library using ctypes. Library functions may be called just like Python functions,
    but any data passed to these functions must be C-compatible types from the ctypes module.

    Only loads libraries located inside the 'lib' folder.

    Returns
    -------
    WinDLL
        an instance of WinDLL representing access to the library
    """
    old_dir = os.getcwd()
    lib_dir = path.join(path.abspath(path.dirname(__file__)), 'lib')
    os.chdir(lib_dir)
    lib = windll.LoadLibrary(name)
    os.chdir(old_dir)
    return lib
