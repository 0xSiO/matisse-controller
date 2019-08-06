import os
from ctypes import *
from os import path


def load_lib(name: str) -> WinDLL:
    old_dir = os.getcwd()
    lib_dir = path.join(path.abspath(path.dirname(__file__)), 'lib')
    os.chdir(lib_dir)
    lib = windll.LoadLibrary(name)
    os.chdir(old_dir)
    return lib
