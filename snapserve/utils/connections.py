import time
import socket
import requests


def wait_for_connection(url: str, timeout: int = 5, max_retries: int = None) -> bool:
    retries = 0
    while True:
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            print(f"Connection to {url} failed, retrying in {timeout} seconds...")
            time.sleep(timeout)
            retries += 1
        if max_retries is not None and retries >= max_retries:
            break
    return False

def is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0