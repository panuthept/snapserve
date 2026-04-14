import inspect


def get_attr_type(attr) -> str:
    if inspect.isfunction(attr):
        return "function"
    elif inspect.isclass(attr):
        return "class"
    else:
        return "object"