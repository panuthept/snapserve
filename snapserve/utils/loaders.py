import os
import sys
import importlib
from types import ModuleType


def load_module(module_path: str, working_dir: str = None) -> ModuleType:
    if ":" not in module_path or module_path.count(":") > 1:
        raise ValueError(f"Module path '{module_path}' is invalid. It should be in the format 'module_path:variable_name'.")
    
    # Add the current working directory to sys.path to allow importing from there
    working_dir = working_dir or os.getcwd()
    sys.path.insert(0, working_dir)
    
    module_path, _ = module_path.split(":")
    module = importlib.import_module(module_path)
    return module