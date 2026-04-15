import json
import typer
from typing import Annotated
from snapserve.consts import CONFIG_DIR
from snapserve.cli.ps import ps_command
from snapserve.cli.serve import serve_command


start_app = typer.Typer()
@start_app.command("start")
def start_command(
    server_id: Annotated[str, typer.Argument(..., help="The ID of the server to start.")],
    host: Annotated[str, typer.Option("--host", "-h", help="The host to bind the server to.")] = None,
    port: Annotated[int, typer.Option("--port", "-p", help="The port to bind the server to.")] = None,
):
    """
    Start a snapserve server.
    """
    running_servers = ps_command(silent=True)

    # Check if server_id is already running
    if server_id in running_servers:
        print(f"Server {server_id} is already running")
        return
    
    # Load config
    config_file = CONFIG_DIR / f"{server_id}.json"
    if not config_file.exists():
        print(f"Config for server {server_id} not found")
        return
    with config_file.open() as f:
        config = json.load(f)

    # Override config with CLI args
    config["host"] = host or config["host"]
    config["port"] = port or config["port"]

    # Start server
    serve_command(
        **config,
        server_id=server_id,
        daemon=True,
    )