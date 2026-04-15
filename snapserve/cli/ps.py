import os
import typer
from snapserve.global_variables import PID_DIR


ps_app = typer.Typer()
@ps_app.command("ps")
def ps_command() -> dict[str, int]:
    """
    List all running snapserve servers.
    """
    running_servers = {}
    for pid_file in PID_DIR.glob("*.pid"):
        process_id = pid_file.stem
        pid = int(pid_file.read_text())
        try:
            os.kill(pid, 0)
            print(f"Server {process_id} is running with PID {pid}")
            running_servers[process_id] = pid
        except ProcessLookupError:
            print(f"Server {process_id} is not running")
    return running_servers