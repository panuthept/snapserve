import os
import typer
from typing import Annotated
from snapserve.global_variables import PID_DIR


stop_app = typer.Typer()
@stop_app.command("stop")
def stop_command(
    server_id: Annotated[str, typer.Argument(..., help="The ID of the server to stop.")],
):
    """
    Stop a running snapserve server.
    """
    pid_file = PID_DIR / f"{server_id}.pid"
    if not pid_file.exists():
        print(f"Server {server_id} is not running")
        return

    pid = int(pid_file.read_text())
    try:
        os.kill(pid, 15)  # Send SIGTERM
        print(f"Server {server_id} stopped")
    except ProcessLookupError:
        print(f"Server {server_id} is not running")
    pid_file.unlink()