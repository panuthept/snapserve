import uuid
import requests
from typing import Any

    
class Remote:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self._base_url = base_url
        self._context_id = uuid.uuid4().hex

    def __getattr__(self, name: str) -> Any:
        response = requests.get(
            f"{self._base_url}/attribute", 
            json={
                "context_id": self._context_id,
                "attr_name": name,
                "attr_path": []
            }
        )
        response.raise_for_status()

        # This will return the value immediately if it's a variable, or return a RemoteAttribute for functions, classes, and objects
        if "value" in response.json():
            return response.json()["value"]
        else:
            return _RemoteAttribute(name, self._base_url, context_id=self._context_id)
        
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        response = requests.delete(
            f"{self._base_url}/attribute", 
            json={"context_id": self._context_id}
        )
        response.raise_for_status()

class _RemoteAttribute:
    def __init__(
        self, 
        name: str, 
        base_url: str = "http://localhost:8000",
        path: list[str] = None,
        context_id: str = None
    ):
        self._id = id
        self._name = name
        self._base_url = base_url
        self._path = path or []
        self._context_id = context_id or uuid.uuid4().hex

    def __repr__(self):
        return f"<RemoteAttribute name={self._name} url={self._base_url} path={self._path}>"

    def __call__(self, *args, **kwargs):
        response = requests.post(
            f"{self._base_url}/attribute", 
            json={
                "context_id": self._context_id,
                "attr_name": self._name,
                "attr_path": self._path,
                "args": args,
                "kwargs": kwargs
            }
        )
        response.raise_for_status()

        # This will return the value immediately if it's a variable, or return a RemoteAttribute for a new object created by a function or class instantiation
        if "value" in response.json():
            return response.json()["value"]
        else:
            return _RemoteAttribute(response.json()["new_name"], self._base_url, context_id=self._context_id)

    def __getattr__(self, attr_name: str):
        path = self._path + [attr_name]
        response = requests.get(
            f"{self._base_url}/attribute", 
            json={
                "context_id": self._context_id,
                "attr_name": self._name,
                "attr_path": path,
            }
        )
        response.raise_for_status()

        # This will return the value immediately if it's a variable, or return a RemoteAttribute for functions, classes, and objects
        if "value" in response.json():
            return response.json()["value"]
        else:
            return _RemoteAttribute(self._name, self._base_url, path=path, context_id=self._context_id)