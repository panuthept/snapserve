import requests
from functools import partial


def validate_endpoint(endpoint: str, base_url: str = "http://localhost:8000"):
    url = f"{base_url}/{endpoint}"
    try:
        response = requests.options(url)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Endpoint '{endpoint}' is not available at {base_url}") from e

def get_client(endpoint: str, base_url: str = "http://localhost:8000") -> "Client":
    url = f"{base_url}/{endpoint}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    attr_type = data.get("type")
    if attr_type == "function":
        return FunctionClient(endpoint, base_url)
    elif attr_type == "class":
        return ClassClient(endpoint, base_url)
    elif attr_type == "object":
        return ObjectClient(
            endpoint=endpoint, 
            base_url=base_url, 
            methods=data.get("methods", []), 
            attributes=data.get("attributes", [])
        )
    else:
        raise ValueError(f"Unsupported attribute type: {attr_type}")

def remote(endpoint: str, base_url: str = "http://localhost:8000") -> "Client":
    validate_endpoint(endpoint, base_url)
    return get_client(endpoint, base_url)

class Client:
    def __init__(self, endpoint: str, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.endpoint = endpoint
    
class FunctionClient(Client):
    def __call__(self, *args, **kwargs):
        payload = {"args": args, "kwargs": kwargs}
        url = f"{self.base_url}/{self.endpoint}"
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["result"]

class ClassClient(Client):
    pass

class ObjectClient(Client):
    def __init__(
        self, 
        endpoint: str, 
        base_url: str = "http://localhost:8000",
        methods: list[str] = None,
        attributes: list[str] = None,
    ):
        super().__init__(endpoint, base_url)
        self.methods = methods or []
        self.attributes = attributes or []

    def __call__(self, *args, **kwargs):
        if "__call__" not in self.methods:
            raise AttributeError(f"Object does not have a __call__ method.")
        return self._call_method("__call__", self.endpoint, self.base_url, *args, **kwargs)

    def __getattr__(self, method_or_attribute_name: str):
        if method_or_attribute_name not in self.methods and method_or_attribute_name not in self.attributes:
            raise AttributeError(f"Object does not have a method or attribute named '{method_or_attribute_name}'.")
        
        if method_or_attribute_name in self.methods:
            return partial(self._call_method, method_or_attribute_name, self.endpoint, self.base_url)
        else:
            return self._get_attribute(method_or_attribute_name, self.endpoint, self.base_url)
    
    @staticmethod
    def _call_method(method_name: str, endpoint: str, base_url: str, *args, **kwargs):
        url = f"{base_url}/{endpoint}"
        payload = {"method_or_attribute_name": method_name, "args": args, "kwargs": kwargs}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["result"]
    
    @staticmethod
    def _get_attribute(attr_name: str, endpoint: str, base_url: str):
        url = f"{base_url}/{endpoint}"
        payload = {"method_or_attribute_name": attr_name}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["result"]