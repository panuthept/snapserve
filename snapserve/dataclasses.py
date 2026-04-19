import inspect
from typing import Any
from dataclasses import dataclass
    

@dataclass
class Attribute:
    attr: Any

@dataclass
class Variable(Attribute):
    pass

@dataclass
class Function(Attribute):
    signature: str = ""
    
    def __post_init__(self):
        self.signature = str(inspect.signature(self.attr))

@dataclass
class Method(Function):
    parent_class: str = ""
    
    def __post_init__(self):
        self.parent_class = self.attr.__self__.__class__.__name__

@dataclass
class Property(Variable):
    parent_class: str = ""

    def __post_init__(self):
        self.parent_class = self.attr.__self__.__class__.__name__

@dataclass
class Class(Attribute):
    init_signature: str = ""
    methods: list[Method] = None
    properties: list[Property] = None

    def __post_init__(self):
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
        self.methods = [
            Method(attr=value) for name, value in inspect.getmembers(self.attr, predicate=inspect.isfunction)
            if name == "__call__" or (not name.startswith("__") and not name.endswith("__"))
        ]
        # Get properties
        self.properties = [
            Property(attr=value) for name, value in inspect.getmembers(self.attr) 
            if isinstance(value, property)  
        ]

@dataclass
class Object(Attribute):
    class_name: str = ""
    init_params: str = ""
    methods: list[Method] = None
    properties: list[Property] = None

    def __post_init__(self):
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
        self.methods = [
            Method(attr=value) for name, value in inspect.getmembers(self.attr, predicate=inspect.ismethod)
            if name == "__call__" or (not name.startswith("__") and not name.endswith("__"))
        ]
        # Get properties
        self.properties = [
            Property(attr=value) for name, value in inspect.getmembers(self.attr) 
            if isinstance(value, property)  
        ]

# @dataclass
# class Attribute:
#     attr: Any
#     type: str = ""
#     signature: str = ""
#     methods: list[str] = None
#     attributes: list[str] = None
    
#     def __post_init__(self):
#         self.type = get_attr_type(self.attr)
#         if self.type == "function":
#             self.signature = str(inspect.signature(self.attr))
#         elif self.type == "class":
#             sig = inspect.signature(self.attr.__init__)
#             params = list(sig.parameters.values())
#             parts = []
#             for param in params:
#                 if param.name == "self":
#                     continue
#                 if hasattr(self.attr, param.name):
#                     value = getattr(self.attr, param.name)
#                     parts.append(f"{param.name}={value!r}")
#             self.signature = f"({", ".join(parts)})"
#         elif self.type == "object":
#             class_name = self.attr.__class__.__name__
#             sig = inspect.signature(self.attr.__init__)
#             params = list(sig.parameters.values())
#             parts = []
#             for param in params:
#                 if hasattr(self.attr, param.name):
#                     value = getattr(self.attr, param.name)
#                     parts.append(f"{param.name}={value!r}")
#             class_params = f"({", ".join(parts)})"
#             self.signature = f"{class_name}{class_params}"

#             self.methods = [
#                 name for name, value in inspect.getmembers(self.attr, predicate=inspect.ismethod)
#                 if name == "__call__" or (not name.startswith("__") and not name.endswith("__"))
#             ]
#             self.attributes = [
#                 name for name, value in inspect.getmembers(self.attr) 
#                 if not callable(value) and (not name.startswith("__") and not name.endswith("__"))
#             ]