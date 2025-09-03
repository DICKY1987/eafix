from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from import_export import load_yaml_flow
from import_export.exporters import export_drawio

def run(command: str="drawio", **kwargs) -> Dict[str, Any]:
    if command != "drawio":
        return {"ok": False, "error": f"unknown command: {command}"}
    input_file: Path = Path(kwargs.get("input_file"))
    output_file: Path|None = kwargs.get("output_file")

    flow = load_yaml_flow(input_file)
    xml = export_drawio(flow)
    out = output_file or input_file.with_suffix(".drawio")
    out.write_text(xml, encoding="utf-8")
    return {"ok": True, "artifact": str(out)}

if __name__ == "__main__":
    import json
    print(json.dumps(run(input_file=Path("specs/demo_atomic.yaml")), indent=2))