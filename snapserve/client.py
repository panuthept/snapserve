import requests
from typing import Any


def remote(name: str, base_url: str = "http://localhost:8000") -> Any:
    response = requests.get(
        f"{base_url}/attribute", 
        json={"attr_name": name}
    )
    response.raise_for_status()

    # This will return the value immediately if it's a variable, or return a RemoteAttribute for functions, classes, and objects
    if "value" in response.json():
        return response.json()["value"]
    else:
        return RemoteAttribute(name, base_url)

class RemoteAttribute:
    def __init__(
        self, 
        name: str, 
        base_url: str = "http://localhost:8000",
        path: list[str] = None,
    ):
        self._name = name
        self._base_url = base_url
        self._path = path or []

    def __repr__(self):
        return f"<RemoteAttribute name={self._name} base_url={self._base_url} path={self._path}>"

    def __call__(self, *args, **kwargs):
        response = requests.post(
            f"{self._base_url}/attribute", 
            json={
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
            return RemoteAttribute(response.json()["new_name"], self._base_url)

    def __getattr__(self, attr_name: str):
        response = requests.get(
            f"{self._base_url}/attribute", 
            json={
                "attr_name": self._name,
                "attr_path": self._path + [attr_name],
            }
        )
        response.raise_for_status()

        # This will return the value immediately if it's a variable, or return a RemoteAttribute for functions, classes, and objects
        if "value" in response.json():
            return response.json()["value"]
        else:
            return RemoteAttribute(self._name, self._base_url, self._path + [attr_name])