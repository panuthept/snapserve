import uuid
import base64
import pickle
from typing import Any
from snapserve.client import Client
from snapserve.utils.attribute import set_remote_attribute


class Remote:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self._context_id = None
        self._client = Client(base_url)

    def __getattr__(self, name: str) -> Any:
        response = self._client.get(
            context_id=self._context_id,
            attr_name=name,
            attr_path=[]
        )
        if "error" in response:
            raise AttributeError(response["error"])
        # This will return the value immediately if it's a variable, or return a RemoteAttribute for functions, classes, and objects
        if "value" in response:
            return response["value"]
        elif "encoded_value" in response:
            return pickle.loads(base64.b64decode(response["encoded_value"]))
        else:
            return _RemoteAttribute(name, self._client, context_id=self._context_id)
        
    def __setattr__(self, name: str, value: Any):
        if name in {"_context_id", "_client"}:
            super().__setattr__(name, value)
            return
        raise AttributeError("Remote attributes are read-only. To modify them, use the Mutable wrapper.")
        
    def __enter__(self):
        self._context_id = uuid.uuid4().hex
        return self

    def __exit__(self, exc_type, exc, tb):
        self._client.delete(context_id=self._context_id)

class _RemoteAttribute:
    def __init__(
        self, 
        name: str, 
        client: Client,
        path: list[str] = None,
        context_id: str = None,
    ):
        self._name = name
        self._client = client
        self._path = path or []
        self._context_id = context_id or uuid.uuid4().hex
        self._mutable = False

    def __repr__(self):
        response = self._client.get(
            context_id=self._context_id,
            attr_name=self._name,
            attr_path=self._path,
        )
        return response["repr"]

    def __call__(self, *args, **kwargs):
        response = self._client.post(
            context_id=self._context_id,
            attr_name=self._name,
            attr_path=self._path,
            args=args,
            kwargs=kwargs
        )
        if "error" in response:
            raise AttributeError(response["error"])
        # This will return the value immediately if it's a variable, or return a RemoteAttribute for a new object created by a function or class instantiation
        if "value" in response:
            return response["value"]
        elif "encoded_value" in response:
            return pickle.loads(base64.b64decode(response["encoded_value"]))
        else:
            return _RemoteAttribute(response["new_name"], self._client, context_id=self._context_id)
    
    def __getattr__(self, name: str):
        path = self._path + [name]
        response = self._client.get(
            context_id=self._context_id,
            attr_name=self._name,
            attr_path=path,
        )
        if "error" in response:
            raise AttributeError(response["error"])
        # This will return the value immediately if it's a variable, or return a RemoteAttribute for functions, classes, and objects
        if "value" in response:
            return response["value"]
        elif "encoded_value" in response:
            return pickle.loads(base64.b64decode(response["encoded_value"]))
        else:
            return _RemoteAttribute(self._name, self._client, path=path, context_id=self._context_id)
        
    def __setattr__(self, name: str, value: Any):
        if name in {"_name", "_client", "_path", "_context_id", "_mutable"}:
            super().__setattr__(name, value)
            return
        
        if not self._mutable:
            raise AttributeError("Remote attributes are read-only. To modify them, use the Mutable wrapper.")
        
        path = self._path + [name]
        set_remote_attribute(self._client, self._context_id, self._name, path, value)