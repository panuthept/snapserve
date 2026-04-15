import os
import uuid
import typer
import subprocess
from typing import Annotated
from snapserve.server import Server
from snapserve.dataclasses import Attribute
from snapserve.loaders import load_attributes
from snapserve.global_variables import PID_DIR, LOG_DIR


serve_app = typer.Typer()
@serve_app.command("serve")
def serve_command(
    module_path: Annotated[str, typer.Argument(..., help="The path to the module to serve, in the format 'module_path:variable_name'.")],
    host: Annotated[str, typer.Option("--host", "-h", help="The host to bind the server to.")] = "localhost",
    port: Annotated[int, typer.Option("--port", "-p", help="The port to bind the server to.")] = 8000,
    workers: Annotated[int, typer.Option("--workers", "-w", help="The number of worker processes to use.")] = None,
    max_concurrency: Annotated[int, typer.Option("--max-concurrency", "-m", help="The maximum number of concurrent requests to allow.")] = None,
    timeout: Annotated[int, typer.Option("--timeout", "-t", help="The timeout for requests in seconds.")] = None,
    cachable: Annotated[bool, typer.Option("--cacheable", "-c", is_flag=True, help="Whether to enable caching for the served application.")] = False,
    cache_size: Annotated[int, typer.Option("--cache-size", help="The maximum size of the cache.")] = 1024,
    daemon: Annotated[bool, typer.Option("--daemon", "-d", is_flag=True, help="Whether to run the server in daemon mode.")] = False,
):
    """
    Serve Python functions, classes, and objects as an API.
    """
    if daemon:
        cmd = [
            "snapserve",
            "serve",
            module_path,
            "--host", host,
            "--port", str(port),
        ]
        if workers is not None:
            cmd.extend(["--workers", str(workers)])
        if max_concurrency is not None:
            cmd.extend(["--max-concurrency", str(max_concurrency)])
        if timeout is not None:
            cmd.extend(["--timeout", str(timeout)])
        if cachable:
            cmd.append("--cacheable")
        if cache_size != 1024:
            cmd.extend(["--cache-size", str(cache_size)])
        
        server_id = uuid.uuid4().hex
        pid_file = PID_DIR / f"{server_id}.pid"
        log_file = LOG_DIR / f"{server_id}.log"

        with open(log_file, "ab", buffering=0) as log:
            process = subprocess.Popen(
                cmd, 
                stdin=subprocess.DEVNULL,
                stdout=log, 
                stderr=log,
                start_new_session=True,
                close_fds=True,
                cwd=os.getcwd(),
            )

        pid_file.write_text(str(process.pid))
        print(f"Server {server_id} started in daemon mode on: http://{host}:{port}")
        return
    
    attributes: dict[str, Attribute] = load_attributes(module_path)
    server = Server(
        attributes=attributes,
        host=host,
        port=port,
        workers=workers,
        max_concurrency=max_concurrency,
        timeout=timeout,
        cachable=cachable,
        cache_size=cache_size,
    )
    server.run()