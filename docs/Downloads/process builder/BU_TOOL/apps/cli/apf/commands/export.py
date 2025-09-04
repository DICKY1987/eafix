import typer
from pathlib import Path
from import_export import load_yaml_flow
from import_export.exporters import export_markdown, export_json, export_yaml, export_drawio
from apf_core.validation import validate_flow
from apf_core import load_registries

app = typer.Typer(no_args_is_help=True)

SUPPORTED = {"md": export_markdown, "json": export_json, "yaml": export_yaml, "drawio": export_drawio}

@app.command()
def run(input: Path = typer.Argument(..., exists=True, readable=True, help="Input APF YAML spec"),
        format: str = typer.Option("md,drawio,json,yaml", "--format", "-f", help="Comma-separated formats"),
        output_dir: Path = typer.Option(Path("derived"), "--output-dir", "-o", help="Output directory"),
        validate: bool = typer.Option(True, "--validate/--no-validate"),
        verbose: bool = typer.Option(False, "--verbose", "-v")):
    """
    Export artifacts from a ProcessFlow YAML using real exporters.
    """
    flow = load_yaml_flow(input)

    if validate:
        diags = validate_flow(flow, Path("."))
        for d in diags:
            level = d["severity"]
            if level in ("ERROR", "WARN") or verbose:
                typer.echo(f"{d['severity']:5} {d['code']}  {d['message']}  ({d.get('location',{}).get('step_id','')})")
        # continue even if errors; user may want artifacts for debugging

    output_dir.mkdir(parents=True, exist_ok=True)
    formats = [x.strip() for x in format.split(",") if x.strip()]
    for fmt in formats:
        if fmt not in SUPPORTED:
            raise typer.BadParameter(f"Unsupported format: {fmt}. Supported: {', '.join(SUPPORTED)}")
        emitter = SUPPORTED[fmt]
        content = emitter(flow)
        suffix = ".drawio" if fmt == "drawio" else f".{fmt}"
        out = output_dir / f"{input.stem}{suffix}"
        out.write_text(content, encoding="utf-8")
        if verbose:
            typer.echo(f"Wrote {out}")
    typer.echo("Export complete.")