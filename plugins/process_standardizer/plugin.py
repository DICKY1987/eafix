from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import yaml
from import_export import load_yaml_flow
from import_export.loaders import dump_yaml_flow

def _load_registry(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))

def _alias_map(reg: dict, key: str) -> Dict[str, str]:
    # Build lowercased alias->id map
    out = {}
    for item in reg.get(key, []):
        canonical = item["id"]
        out[canonical.lower()] = canonical
        for a in (item.get("aliases") or []) + (item.get("synonyms") or []):
            out[a.lower()] = canonical
    return out

def run(command: str="normalize", **kwargs) -> Dict[str, Any]:
    if command != "normalize":
        return {"ok": False, "error": f"unknown command: {command}"}

    input_file: Path = Path(kwargs.get("input_file"))
    output_file: Path|None = kwargs.get("output_file")
    dry: bool = bool(kwargs.get("dry_run", False))

    flow = load_yaml_flow(input_file)
    actions_reg = _load_registry(Path("registries/actions.yaml"))
    actors_reg = _load_registry(Path("registries/actors.yaml"))

    action_map = _alias_map(actions_reg, "actions")
    actor_map = _alias_map(actors_reg, "actors")

    diags: List[dict] = []
    for s in flow.steps:
        ca = action_map.get(s.action.lower())
        if ca and ca != s.action:
            diags.append({"severity": "INFO", "code": "APF0401", "message": f"action alias '{s.action}' → '{ca}'", "location": {"step_id": s.id}})
            s.action = ca
        ca2 = actor_map.get(s.actor.lower())
        if ca2 and ca2 != s.actor:
            diags.append({"severity": "INFO", "code": "APF0402", "message": f"actor alias '{s.actor}' → '{ca2}'", "location": {"step_id": s.id}})
            s.actor = ca2

    if not dry:
        target = output_file or input_file
        target.write_text(dump_yaml_flow(flow), encoding="utf-8")

    return {"ok": True, "diagnostics": diags}

if __name__ == "__main__":
    import json
    print(json.dumps(run(input_file=Path("specs/demo_atomic.yaml"), dry_run=True), indent=2))