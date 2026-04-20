import requests
from typing import Any
from functools import partial


def remote(name: str, base_url: str = "http://localhost:8000") -> Any:
    url = f"{base_url}/attribute"
    payload = {"attr_name": name}

    response = requests.get(url, json=payload)
    response.raise_for_status()
    data = response.json()

    if data["type"] == "variable":
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["value"]
    elif data["type"] == "function":
        return FunctionClient(name, base_url)
    elif data["type"] == "class":
        return ClassClient(name, base_url)
    elif data["type"] == "object":
        return ObjectClient(
            name=name, 
            base_url=base_url, 
            methods=data.get("methods", []), 
            properties=data.get("properties", [])
        )

class Client:
    def __init__(self, name: str, base_url: str = "http://localhost:8000"):
        self.name = name
        self.base_url = base_url
    
class FunctionClient(Client):
    def __call__(self, *args, **kwargs):
        url = f"{self.base_url}/attribute"
        payload = {"attr_name": self.name, "args": args, "kwargs": kwargs}

        response = requests.post(url, json=payload)
        response.raise_for_status()

        if "value" in response.json():
            return response.json()["value"]
        else:
            return remote(response.json()["new_attr_name"], base_url=self.base_url)
        
class ClassClient(Client):
    def __call__(self, *args, **kwargs):
        url = f"{self.base_url}/attribute"
        payload = {"attr_name": self.name, "args": args, "kwargs": kwargs}

        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return remote(response.json()["new_attr_name"], base_url=self.base_url)

class ObjectClient(Client):
    def __init__(
        self, 
        endpoint: str, 
        base_url: str = "http://localhost:8000",
        methods: list[str] = None,
        properties: list[str] = None,
        obj_id: str = None
    ):
        super().__init__(endpoint, base_url)
        self.methods = methods or []
        self.properties = properties or []
        self.obj_id = obj_id

    def __call__(self, *args, **kwargs):
        if "__call__" not in self.methods:
            raise AttributeError(f"Object does not have a __call__ method.")
        return self._call_method(self.obj_id, "__call__", self.endpoint, self.base_url, *args, **kwargs)

    def __getattr__(self, method_or_attribute_name: str):
        if method_or_attribute_name not in self.methods and method_or_attribute_name not in self.attributes:
            raise AttributeError(f"Object does not have a method or attribute named '{method_or_attribute_name}'.")
        
        if method_or_attribute_name in self.methods:
            return partial(self._call_method, self.obj_id, method_or_attribute_name, self.endpoint, self.base_url)
        else:
            return self._get_attribute(self.obj_id, method_or_attribute_name, self.endpoint, self.base_url)
    
    @staticmethod
    def _call_method(obj_id: str, method_name: str, endpoint: str, base_url: str, *args, **kwargs):
        url = f"{base_url}/{endpoint}"
        payload = {"id": obj_id, "method_or_attribute_name": method_name, "args": args, "kwargs": kwargs}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["result"]
    
    @staticmethod
    def _get_attribute(obj_id: str, attr_name: str, endpoint: str, base_url: str):
        url = f"{base_url}/{endpoint}"
        payload = {"id": obj_id, "method_or_attribute_name": attr_name}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["result"]