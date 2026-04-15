import requests
from functools import partial


def get_client(endpoint: str, base_url: str = "http://localhost:8000") -> "Client":
    url = f"{base_url}/{endpoint}"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Endpoint '{endpoint}' is not available at {base_url}") from e
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

class ObjectClient(Client):
    def __init__(
        self, 
        endpoint: str, 
        base_url: str = "http://localhost:8000",
        methods: list[str] = None,
        attributes: list[str] = None,
        obj_id: str = None
    ):
        super().__init__(endpoint, base_url)
        self.methods = methods or []
        self.attributes = attributes or []
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
    
class ClassClient(Client):
    def __call__(self, *args, **kwargs):
        payload = {"args": args, "kwargs": kwargs}
        url = f"{self.base_url}/{self.endpoint}"
        response = requests.post(url, json=payload)
        response.raise_for_status()
        obj_id = response.json()["result"]

        url = f"{self.base_url}/"
        response = requests.get(url)
        response.raise_for_status()
        attribute = response.json()["attributes"][obj_id]
        return ObjectClient(
            endpoint=self.endpoint, 
            base_url=self.base_url, 
            methods=attribute.get("methods", []), 
            attributes=attribute.get("attributes", []),
            obj_id=obj_id
        )