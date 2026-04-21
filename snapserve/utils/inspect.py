import pickle
import base64
import inspect


def get_attr_type(attr) -> str:
    if inspect.isfunction(attr):
        return "function"
    elif inspect.isclass(attr):
        return "class"
    elif callable(attr):
        return "method"
    elif hasattr(attr, "__dict__"):
        return "object"
    else:
        return "variable"
    
def get_attr_info(attr) -> dict:
    attr_type = get_attr_type(attr)
    info = {"type": attr_type}
    
    if attr_type == "function":
        info["signature"] = str(inspect.signature(attr))
    elif attr_type == "class":
        info["init_signature"] = str(inspect.signature(attr.__init__))
        info["methods"] = [name for name, member in inspect.getmembers(attr) if inspect.isfunction(member) and not name.startswith("__")]
        info["properties"] = [name for name, member in inspect.getmembers(attr) if not inspect.isroutine(member) and not name.startswith("__")]
    elif attr_type == "object":
        info["class_name"] = attr.__class__.__name__
        info["init_signature"] = str(inspect.signature(attr.__class__.__init__))
        info["methods"] = [name for name, member in inspect.getmembers(attr) if inspect.isroutine(member) and not name.startswith("__")]
        info["properties"] = [name for name, member in inspect.getmembers(attr) if not inspect.isroutine(member) and not name.startswith("__")]
        sig = inspect.signature(attr.__init__)
        params = list(sig.parameters.values())
        parts = []
        for param in params:
            if hasattr(attr, param.name):
                value = getattr(attr, param.name)
                parts.append(f"{param.name}={value!r}")
        info["params"] = f"({", ".join(parts)})"
    elif attr_type == "variable":
        # Use pickle to serialize the value if it's not a python built-in type
        if isinstance(attr, (int, float, str, bool, list, dict, type(None))):
            info["value"] = attr
        else:
            info["encoded_value"] = base64.b64encode(pickle.dumps(attr)).decode("ascii")
    return info