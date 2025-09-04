import typer
from pathlib import Path
import json

app = typer.Typer(no_args_is_help=True)

@app.command()
def run(input: Path = typer.Argument(..., exists=True, readable=True, help="Input YAML spec"),
        output: Path = typer.Option(None, "--output", "-o", help="Write diagnostics JSON to file"),
        severity: str = typer.Option("info", "--severity", "-s", help="Minimum severity to display"),
        fmt: str = typer.Option("table", "--format", "-f", help="table|json")):
    """
    Validate an APF YAML spec and print diagnostics.
    This is a skeleton emitting a canned result.
    """
    diags = [{
        "severity": "INFO",
        "code": "APF0000",
        "message": "Validator stub executed",
        "location": {"file": str(input)}
    }]
    if output:
        output.write_text(json.dumps(diags, indent=2), encoding="utf-8")
    if fmt == "json":
        typer.echo(json.dumps(diags, indent=2))
    else:
        for d in diags:
            typer.echo(f"{d['severity']:5} {d['code']}  {d['message']}  ({d['location'].get('file','')})")