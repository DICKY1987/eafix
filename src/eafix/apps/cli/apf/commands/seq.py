import typer
from pathlib import Path
import yaml
from import_export import load_yaml_flow
from import_export.loaders import dump_yaml_flow
from apf_core import StepSequencer

app = typer.Typer(no_args_is_help=True)
seq = StepSequencer()

@app.command("insert")
def insert(input: Path = typer.Argument(..., exists=True, readable=True),
           after: str = typer.Option(..., "--after", help="Insert after this StepKey"),
           actor: str = typer.Option("user", "--actor"),
           action: str = typer.Option("transform", "--action"),
           text: str = typer.Option("New step", "--text"),
           dry_run: bool = typer.Option(False, "--dry-run"),
           backup: bool = typer.Option(True, "--backup/--no-backup")):
    """
    Insert a new step after the given StepKey. Computes a legal StepKey midpoint or next.
    """
    flow = load_yaml_flow(input)
    ids = [s.id for s in flow.steps]
    new_id = seq.insert_after(ids, after)
    # Build the new step and insert
    idx = ids.index(after) + 1
    step = type(flow.steps[0])(id=new_id, actor=actor, action=action, text=text, next=[])

    if not dry_run:
        flow.steps.insert(idx, step)
        if backup:
            backup_path = input.with_suffix(".bak.yaml")
            backup_path.write_text(input.read_text(encoding="utf-8"), encoding="utf-8")
        input.write_text(dump_yaml_flow(flow), encoding="utf-8")

    typer.echo(f"Inserted step {new_id} after {after}. (dry_run={dry_run})")

@app.command("renumber")
def renumber(input: Path = typer.Argument(..., exists=True, readable=True),
             start: str = typer.Option("1.001", "--start"),
             increment: str = typer.Option("0.001", "--increment"),
             dry_run: bool = typer.Option(False, "--dry-run"),
             backup: bool = typer.Option(True, "--backup/--no-backup")):
    """
    Renumber steps to canonical precision and rewrite the YAML.
    """
    flow = load_yaml_flow(input)
    old_ids = [s.id for s in flow.steps]
    new_ids = seq.renumber(old_ids, start=start, increment=increment)
    id_map = dict(zip(old_ids, new_ids))
    for s in flow.steps:
        s.id = id_map[s.id]
        if s.next:
            s.next = [id_map.get(n, n) for n in s.next]

    if not dry_run:
        if backup:
            backup_path = input.with_suffix(".bak.yaml")
            backup_path.write_text(input.read_text(encoding="utf-8"), encoding="utf-8")
        input.write_text(dump_yaml_flow(flow), encoding="utf-8")

    typer.echo(f"Renumbered {len(old_ids)} steps starting at {start} (+{increment}). (dry_run={dry_run})")