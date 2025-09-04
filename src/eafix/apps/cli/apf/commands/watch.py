import typer
from pathlib import Path

app = typer.Typer(no_args_is_help=True)

@app.command()
def run(directory: Path = typer.Argument(".", exists=True, file_okay=False),
        patterns: str = typer.Option("*.yaml", "--patterns"),
        debounce_ms: int = typer.Option(500, "--debounce", help="Debounce in milliseconds")):
    """
    Watch a directory and regenerate artifacts on change (skeleton).
    """
    typer.echo(f"[stub] watching {directory} for {patterns} (debounce {debounce_ms}ms)")