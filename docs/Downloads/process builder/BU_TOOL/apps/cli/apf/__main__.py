# Typer-based CLI wiring
import sys
import typer

app = typer.Typer(add_completion=False, help="APF command-line interface")

# Subcommands live in apf.commands.* and are imported lazily
from .commands import export as _export
from .commands import validate as _validate
from .commands import seq as _seq
from .commands import watch as _watch

app.add_typer(_export.app, name="export", help="Export artifacts from a YAML spec")
app.add_typer(_validate.app, name="validate", help="Validate a YAML spec (schema + semantics)")
app.add_typer(_seq.app, name="seq", help="Step sequencing operations (insert/renumber)")
app.add_typer(_watch.app, name="watch", help="Watch a directory and regenerate artifacts")

def main():
    try:
        app()
    except Exception as e:
        typer.echo(f"ERROR: {e}", err=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    main()