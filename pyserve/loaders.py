from pyserve.dataclasses import Attribute
from pyserve.utils.loaders import load_module


def load_attributes(module_path: str) -> dict[str, Attribute]:
    module = load_module(module_path)
    
    attributes = {}
    for attr_name in module_path.split(":")[1].split(","):
        attr_name = attr_name.strip()
        if not hasattr(module, attr_name):
            raise AttributeError(f"Module '{module.__name__}' does not have an attribute named '{attr_name}'.")
        attr = getattr(module, attr_name)
        attributes[attr_name] = Attribute(attr, attr_name)
    
    return attributes