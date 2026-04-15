import os
import json
import typer
from snapserve.consts import PID_DIR, CONFIG_DIR


ps_app = typer.Typer()
@ps_app.command("ps")
def ps_command() -> dict[str, int]:
    """
    List all running snapserve servers.
    """
    print("SERVER ID                            PID       STATUS     URL")
    running_servers = {}
    for pid_file in PID_DIR.glob("*.pid"):
        process_id = pid_file.stem
        pid = int(pid_file.read_text())
        config_file = CONFIG_DIR / f"{process_id}.json"
        url = "N/A"
        if config_file.exists():
            with config_file.open() as f:
                config = json.load(f)
                url = f"http://{config['host']}:{config['port']}"
        try:
            os.kill(pid, 0)
            print(f"{process_id}     {pid}     ONLINE     {url}")
            running_servers[process_id] = pid
        except ProcessLookupError:
            print(f"{process_id}     {pid}     OFFLINE    N/A")
    return running_servers