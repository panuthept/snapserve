import typer
from .serve import serve_app


app = typer.Typer()
app.add_typer(serve_app)