import inspect
from typing import Any
from dataclasses import dataclass
from pyserve.utils.inspect import get_attr_type


@dataclass
class Attribute:
    attr: Any
    type: str = ""
    signature: str = ""
    
    def __post_init__(self):
        self.type = get_attr_type(self.attr)
        if self.type == "function":
            self.signature = str(inspect.signature(self.attr))
        elif self.type == "class":
            self.signature = str(inspect.signature(self.attr.__init__))
        elif self.type == "object":
            class_name = self.attr.__class__.__name__
            sig = inspect.signature(self.attr.__init__)
            params = list(sig.parameters.values())
            parts = []
            for param in params:
                if hasattr(self.attr, param.name):
                    value = getattr(self.attr, param.name)
                    parts.append(f"{param.name}={value!r}")
            class_params = f"({", ".join(parts)})"
            self.signature = f"{class_name}{class_params}"