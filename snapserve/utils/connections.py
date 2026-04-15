import time
import socket
import requests


def wait_for_connection(url: str, timeout: int = 1, max_wait: int = 15) -> bool:
    for _ in range(max_wait * 2):  # ~max_wait seconds max
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            time.sleep(0.5)
    return False

def is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0