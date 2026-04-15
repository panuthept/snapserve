import typer
from .ps import ps_app
from .stop import stop_app
from .serve import serve_app


app = typer.Typer()
app.add_typer(ps_app)
app.add_typer(stop_app)
app.add_typer(serve_app)