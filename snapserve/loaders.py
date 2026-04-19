from snapserve.utils.loaders import load_module
from snapserve.utils.inspect import get_attr_type
from snapserve.dataclasses import Attribute, Function, Method, Class, Object, Variable


def load_attributes(module_path: str, working_dir: str = None) -> dict[str, Attribute]:
    module = load_module(module_path, working_dir=working_dir)
    
    attributes = {}
    for attr_name in module_path.split(":")[1].split(","):
        attr_name = attr_name.strip()
        if not hasattr(module, attr_name):
            raise AttributeError(f"Module '{module.__name__}' does not have an attribute named '{attr_name}'.")
        attr = getattr(module, attr_name)
        type = get_attr_type(attr)
        if type == "function":
            attributes[attr_name] = Function(attr)
        elif type == "class":
            attributes[attr_name] = Class(attr)
        elif type == "object":
            attributes[attr_name] = Object(attr)
        elif type == "method":
            attributes[attr_name] = Method(attr)
        else:
            attributes[attr_name] = Variable(attr)
    
    return attributes