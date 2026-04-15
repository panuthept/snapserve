import os
import json
import typer
from typing import Annotated
from snapserve.consts import PID_DIR, CONFIG_DIR


ps_app = typer.Typer()
@ps_app.command("ps")
def ps_command(
    silent: Annotated[bool, typer.Option("--silent", is_flag=True, help="Whether to print silent output.")] = False,
) -> dict[str, int]:
    """
    List all running snapserve servers.
    """
    if not silent: print("SERVER ID       PID       STATUS       URL       MODULE")
    running_servers = {}
    for pid_file in PID_DIR.glob("*.pid"):
        process_id = pid_file.stem
        pid = int(pid_file.read_text())
        config_file = CONFIG_DIR / f"{process_id}.json"
        url = "N/A"
        module = "N/A"
        if config_file.exists():
            with config_file.open() as f:
                config = json.load(f)
                url = f"http://{config['host']}:{config['port']}"
                module = config["module_path"]
        try:
            os.kill(pid, 0)
            if not silent: print(f"{process_id}       {pid}       ONLINE       {url}       {module}")
            running_servers[process_id] = pid
        except ProcessLookupError:
            if not silent: print(f"{process_id}       {pid}       OFFLINE       N/A       {module}")
    return running_servers