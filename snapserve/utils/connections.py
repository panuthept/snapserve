import time
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