from snapserve.utils.loaders import load_module
from snapserve.dataclasses import Attribute, AutoAttribute


def load_attributes(module_path: str, working_dir: str = None) -> dict[str, Attribute]:
    module = load_module(module_path, working_dir=working_dir)
    
    attributes = {}
    for attr_name in module_path.split(":")[1].split(","):
        attr_name = attr_name.strip()
        if not hasattr(module, attr_name):
            raise AttributeError(f"Module '{module.__name__}' does not have an attribute named '{attr_name}'.")
        attr = getattr(module, attr_name)
        attributes[attr_name] = AutoAttribute.from_attr(attr)
    
    return attributes