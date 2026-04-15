import os
import json
import uuid
import typer
import logging
import subprocess
from typing import Annotated
from snapserve.server import Server
from snapserve.dataclasses import Attribute
from snapserve.loaders import load_attributes
from snapserve.utils.connections import is_port_in_use
from snapserve.consts import PID_DIR, LOG_DIR, CONFIG_DIR


serve_app = typer.Typer()
@serve_app.command("serve")
def serve_command(
    module_path: Annotated[str, typer.Argument(..., help="The path to the module to serve, in the format 'module_path:variable_name'.")],
    host: Annotated[str, typer.Option("--host", "-h", help="The host to bind the server to.")] = "localhost",
    port: Annotated[int, typer.Option("--port", "-p", help="The port to bind the server to.")] = 8000,
    workers: Annotated[int, typer.Option("--workers", "-w", help="The number of worker processes to use.")] = None,
    max_concurrency: Annotated[int, typer.Option("--max-concurrency", "-m", help="The maximum number of concurrent requests to allow.")] = None,
    timeout: Annotated[int, typer.Option("--timeout", "-t", help="The timeout for requests in seconds.")] = None,
    allow_cache: Annotated[bool, typer.Option("--allow-cache", "-c", is_flag=True, help="Whether to enable caching for the served application.")] = False,
    cache_size: Annotated[int, typer.Option("--cache-size", help="The maximum size of the cache.")] = 1024,
    logging_path: Annotated[str, typer.Option("--logging-path", help="The path to the logging.")] = None,
    working_dir: Annotated[str, typer.Option("--working-dir", help="The working directory to use when loading the module.")] = None,
    server_id: Annotated[str, typer.Option("--server-id", help="The ID of the server to start (only used in daemon mode).")] = None,
    daemon: Annotated[bool, typer.Option("--daemon", "-d", is_flag=True, help="Whether to run the server in daemon mode.")] = False,
):
    """
    Serve Python functions, classes, and objects as an API.
    """
    working_dir = working_dir or os.getcwd()
    if is_port_in_use(host, port):
        raise RuntimeError(f"❌ Port {port} is already in use. Please choose a different port or stop the server using it.")

    if daemon:
        server_id = server_id or uuid.uuid4().hex
        pid_file = PID_DIR / f"{server_id}.pid"
        out_file = LOG_DIR / f"{server_id}.out"
        config_file = CONFIG_DIR / f"{server_id}.json"

        cmd = [
            "snapserve",
            "serve",
            module_path,
            "--host", host,
            "--port", str(port),
            "--logging-path", out_file,
            "--working-dir", working_dir,
        ]
        if workers is not None:
            cmd.extend(["--workers", str(workers)])
        if max_concurrency is not None:
            cmd.extend(["--max-concurrency", str(max_concurrency)])
        if timeout is not None:
            cmd.extend(["--timeout", str(timeout)])
        if allow_cache:
            cmd.append("--allow-cache")
        if cache_size != 1024:
            cmd.extend(["--cache-size", str(cache_size)])
        
        json.dump({
            "working_dir": working_dir,
            "module_path": module_path,
            "host": host,
            "port": port,
            "workers": workers,
            "max_concurrency": max_concurrency,
            "timeout": timeout,
            "allow_cache": allow_cache,
            "cache_size": cache_size,
        }, config_file.open("w"), indent=4)

        process = subprocess.Popen(
            cmd, 
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            start_new_session=True,
            close_fds=True,
            cwd=os.getcwd(),
        )

        pid_file.write_text(str(process.pid))
        print(f"Started {server_id}")
        return

    logging.basicConfig(
        filename=logging_path if logging_path else None,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    attributes: dict[str, Attribute] = load_attributes(module_path, working_dir=working_dir)
    server = Server(
        attributes=attributes,
        host=host,
        port=port,
        workers=workers,
        max_concurrency=max_concurrency,
        timeout=timeout,
        allow_cache=allow_cache,
        cache_size=cache_size,
    )
    server.run()