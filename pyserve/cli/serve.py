import typer
from typing import Annotated
from pyserve.server import Server
from pyserve.dataclasses import Attribute
from pyserve.loaders import load_attributes


serve_app = typer.Typer()
@serve_app.command("serve")
def serve(
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