from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from import_export import load_yaml_flow
from apf_core.validation import validate_flow

def run(command: str="validate", **kwargs) -> Dict[str, Any]:
    if command != "validate":
        return {"ok": False, "error": f"unknown command: {command}"}
    input_file: Path = Path(kwargs.get("input_file"))
    flow = load_yaml_flow(input_file)
    diags = validate_flow(flow, Path("."))
    return {"ok": True, "diagnostics": diags}

if __name__ == "__main__":
    import json
    print(json.dumps(run(input_file=Path("specs/demo_atomic.yaml")), indent=2))