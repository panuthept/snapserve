import uuid
import base64
import pickle
from typing import Any
from snapserve.client import Client
from snapserve.utils.attribute import set_remote_attribute


class Remote:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.__context_id = None
        self.__client = Client(base_url)

    def __getattr__(self, name: str) -> Any:
        response = self.__client.get(
            context_id=self.__context_id,
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
            return RemoteAttribute(name, self.__client, context_id=self.__context_id)
        
    def __setattr__(self, name: str, value: Any):
        if name in {"_Remote__context_id", "_Remote__client"}:
            super().__setattr__(name, value)
            return
        
        set_remote_attribute(self.__client, self.__context_id, name, [], value)
        
    def __enter__(self):
        self.__context_id = uuid.uuid4().hex
        return self

    def __exit__(self, exc_type, exc, tb):
        self.__client.delete(context_id=self.__context_id)

class RemoteAttribute:
    def __init__(
        self, 
        name: str, 
        client: Client,
        path: list[str] = None,
        context_id: str = None,
    ):
        self.__name = name
        self.__client = client
        self.__path = path or []
        self.__context_id = context_id or uuid.uuid4().hex

    def __repr__(self):
        response = self.__client.get(
            context_id=self.__context_id,
            attr_name=self.__name,
            attr_path=self.__path,
        )
        return response["repr"]

    def __call__(self, *args, **kwargs):
        response = self.__client.post(
            context_id=self.__context_id,
            attr_name=self.__name,
            attr_path=self.__path,
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
            return RemoteAttribute(response["new_name"], self.__client, context_id=self.__context_id)
    
    def __getattr__(self, name: str):
        path = self.__path + [name]
        response = self.__client.get(
            context_id=self.__context_id,
            attr_name=self.__name,
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
            return RemoteAttribute(self.__name, self.__client, path=path, context_id=self.__context_id)
        
    def __setattr__(self, name: str, value: Any):
        if name in {"_RemoteAttribute__name", "_RemoteAttribute__client", "_RemoteAttribute__path", "_RemoteAttribute__context_id"}:
            super().__setattr__(name, value)
            return
        
        path = self.__path + [name]
        set_remote_attribute(self.__client, self.__context_id, self.__name, path, value)