from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any

from import_export import load_yaml_flow
from import_export.exporters import export_markdown, export_json, export_yaml, export_drawio
from apf_core.validation import validate_flow

SUPPORTED = {"md": export_markdown, "json": export_json, "yaml": export_yaml, "drawio": export_drawio}

def run(command: str="run", **kwargs) -> Dict[str, Any]:
    if command != "run":
        return {"ok": False, "error": f"unknown command: {command}"}

    input_file: Path = Path(kwargs.get("input_file"))
    formats: List[str] = kwargs.get("formats") or ["md", "drawio", "json", "yaml"]
    output_dir: Path = Path(kwargs.get("output_dir") or "derived")
    do_validate: bool = bool(kwargs.get("validate", True))

    flow = load_yaml_flow(input_file)
    diagnostics = []
    if do_validate:
        diagnostics = validate_flow(flow, Path("."))

    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts: List[str] = []
    for fmt in formats:
        if fmt not in SUPPORTED:
            continue
        content = SUPPORTED[fmt](flow)
        suffix = ".drawio" if fmt == "drawio" else f".{fmt}"
        out = output_dir / f"{input_file.stem}{suffix}"
        out.write_text(content, encoding="utf-8")
        artifacts.append(str(out))

    return {"ok": True, "artifacts": artifacts, "diagnostics": diagnostics}

if __name__ == "__main__":
    # simple manual smoke: python plugin.py specs/demo_atomic.yaml
    import sys, json
    inp = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("specs/demo_atomic.yaml")
    print(json.dumps(run(input_file=inp), indent=2))