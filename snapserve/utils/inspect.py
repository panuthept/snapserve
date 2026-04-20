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