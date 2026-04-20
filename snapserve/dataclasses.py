import inspect
from typing import Any
from dataclasses import dataclass
from snapserve.utils.inspect import get_attr_type


class AutoAttribute:
    @classmethod
    def from_attr(cls, attr: Any) -> "Attribute":
        type = get_attr_type(attr)
        if type == "function":
            return Function(attr)
        elif type == "class":
            return Class(attr)
        elif type == "object":
            return Object(attr)
        else:
            return Variable(attr)

@dataclass
class Attribute:
    attr: Any
    type: str = ""

    def to_dict(self) -> dict:
        return {key: value for key, value in self.__dict__.items() if key != "attr"}
    
    def call(self, *args, **kwargs) -> Any:
        if callable(self.attr):
            return self.attr(*args, **kwargs)
        else:
            return self.attr

@dataclass
class Variable(Attribute):
    def __post_init__(self):
        self.type = "variable"

@dataclass
class Function(Attribute):
    signature: str = ""
    
    def __post_init__(self):
        self.signature = str(inspect.signature(self.attr))
        self.type = "function"

@dataclass
class Class(Attribute):
    init_signature: str = ""
    methods: dict[str, Function] = None
    properties: dict[str, Variable] = None

    def __post_init__(self):
        self.type = "class"
        # Get init signature
        sig = inspect.signature(self.attr.__init__)
        params = list(sig.parameters.values())
        parts = []
        for param in params:
            if param.name == "self":
                continue
            if hasattr(self.attr, param.name):
                value = getattr(self.attr, param.name)
                parts.append(f"{param.name}={value!r}")
        self.init_signature = f"({", ".join(parts)})"
        # Get methods
        self.methods = {
            name: Function(attr=value) for name, value in inspect.getmembers(self.attr, predicate=inspect.isfunction)
            if name == "__call__" or (not name.startswith("__") and not name.endswith("__"))
        }
        # Get properties
        self.properties = {
            name: Variable(attr=value) for name, value in inspect.getmembers(self.attr) 
            if not callable(value) and (not name.startswith("__") and not name.endswith("__"))
        }

@dataclass
class Object(Attribute):
    class_name: str = ""
    init_params: str = ""
    methods: dict[str, Function] = None
    properties: dict[str, Variable] = None

    def __post_init__(self):
        self.type = "object"
        # Get class name
        self.class_name = self.attr.__class__.__name__
        # Get init params
        class_name = self.attr.__class__.__name__
        sig = inspect.signature(self.attr.__init__)
        params = list(sig.parameters.values())
        parts = []
        for param in params:
            if hasattr(self.attr, param.name):
                value = getattr(self.attr, param.name)
                parts.append(f"{param.name}={value!r}")
        class_params = f"({", ".join(parts)})"
        self.init_params = f"{class_name}{class_params}"
        # Get methods
        self.methods = {
            name: Function(attr=value) for name, value in inspect.getmembers(self.attr, predicate=inspect.ismethod)
            if name == "__call__" or (not name.startswith("__") and not name.endswith("__"))
        }
        # Get properties
        self.properties = {
            name: Variable(attr=value) for name, value in inspect.getmembers(self.attr) 
            if not callable(value) and (not name.startswith("__") and not name.endswith("__"))
        }