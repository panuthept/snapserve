import requests


class Client:
    def __init__(self, endpoint: str, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.endpoint = endpoint
        self.validate_endpoint()

    def validate_endpoint(self):
        url = f"{self.base_url}/{self.endpoint}"
        try:
            response = requests.options(url)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ValueError(f"Endpoint '{self.endpoint}' is not available at {self.base_url}") from e

    def __call__(self, *args, **kwargs):
        payload = {"args": args, "kwargs": kwargs}
        url = f"{self.base_url}/{self.endpoint}"
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["result"]