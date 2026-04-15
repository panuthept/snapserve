import os
import typer
from typing import Annotated
from snapserve.cli.ps import ps_command
from snapserve.consts import PID_DIR, CONFIG_DIR


stop_app = typer.Typer()
@stop_app.command("stop")
def stop_command(
    server_id: Annotated[str, typer.Argument(help="The ID of the server to stop.")] = None,
    all: Annotated[bool, typer.Option("--all", "-a", is_flag=True, help="Stop all running servers.")] = False,
    delete: Annotated[bool, typer.Option("--delete", is_flag=True, help="Whether to delete the server config after stopping.")] = False,
):
    """
    Stop a running snapserve server.
    """
    if all:
        running_servers = ps_command(silent=True)
        for server_id in running_servers.keys():
            stop_command(server_id=server_id)
        return
    
    if server_id is None:
        raise ValueError("Please specify a server ID to stop, or use --all to stop all servers.")

    pid_file = PID_DIR / f"{server_id}.pid"
    if not pid_file.exists():
        print(f"Server {server_id} is not running")
        return

    pid = int(pid_file.read_text())
    try:
        os.kill(pid, 15)  # Send SIGTERM
        print(f"Stopped {server_id}")
    except ProcessLookupError:        
        pass
    
    if delete:
        pid_file.unlink()
        config_file = CONFIG_DIR / f"{server_id}.json"
        if config_file.exists():
            config_file.unlink()