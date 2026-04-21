import os
import sys
import importlib
from types import ModuleType


def load_module(module_path: str, working_dir: str = None) -> ModuleType:
    # Add the current working directory to sys.path to allow importing from there
    working_dir = working_dir or os.getcwd()
    sys.path.insert(0, working_dir)
    
    module = importlib.import_module(module_path)
    return module