import requests
from typing import Any
from snapserve.utils.connections import wait_for_connection


class Client:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self._base_url = base_url
        if not wait_for_connection(f"{self._base_url}/"):
            raise RuntimeError(f"❌ Failed to connect to server at {self._base_url}. Please make sure the server is running and try again.")
        
    def get(self, context_id: str, attr_name: str, attr_path: list[str] = None) -> dict:
        response = requests.get(
            f"{self._base_url}/attribute", 
            json={
                "context_id": context_id,
                "attr_name": attr_name,
                "attr_path": attr_path or []
            }
        )
        response.raise_for_status()
        if "error" in response.json():
            raise AttributeError(response.json()["error"])
        return response.json()
    
    def put(self, context_id: str, attr_name: str, attr_path: list[str] = None, **value) -> dict:
        response = requests.put(
            f"{self._base_url}/attribute", 
            json={
                "context_id": context_id,
                "attr_name": attr_name,
                "attr_path": attr_path or [],
                **value,
            }
        )
        response.raise_for_status()
        if "error" in response.json():
            raise AttributeError(response.json()["error"])
        return response.json()
    
    def post(self, context_id: str, attr_name: str, attr_path: list[str] = None, args: list[Any] = None, kwargs: dict[str, Any] = None) -> dict:
        response = requests.post(
            f"{self._base_url}/attribute", 
            json={
                "context_id": context_id,
                "attr_name": attr_name,
                "attr_path": attr_path or [],
                "args": args or [],
                "kwargs": kwargs or {},
            }
        )
        response.raise_for_status()
        if "error" in response.json():
            raise AttributeError(response.json()["error"])
        return response.json()
    
    def delete(self, context_id: str) -> dict:
        response = requests.delete(
            f"{self._base_url}/attribute", 
            json={"context_id": context_id}
        )
        response.raise_for_status()
        if "error" in response.json():
            raise AttributeError(response.json()["error"])
        return response.json()