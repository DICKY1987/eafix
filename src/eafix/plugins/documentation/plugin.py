from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import zipfile, io
from import_export import load_yaml_flow
from import_export.exporters import export_markdown, export_json, export_drawio

def run(command: str="bundle", **kwargs) -> Dict[str, Any]:
    if command != "bundle":
        return {"ok": False, "error": f"unknown command: {command}"}
    input_file: Path = Path(kwargs.get("input_file"))
    output_dir: Path = Path(kwargs.get("output_dir") or "derived")
    formats: List[str] = kwargs.get("formats") or ["md", "drawio", "json"]
    output_dir.mkdir(parents=True, exist_ok=True)

    flow = load_yaml_flow(input_file)
    artifacts = {}

    for fmt in formats:
        if fmt == "md":
            content = export_markdown(flow)
            path = output_dir / f"{input_file.stem}.md"
        elif fmt == "json":
            content = export_json(flow)
            path = output_dir / f"{input_file.stem}.json"
        elif fmt == "drawio":
            content = export_drawio(flow)
            path = output_dir / f"{input_file.stem}.drawio"
        else:
            continue
        path.write_text(content, encoding="utf-8")
        artifacts[path.name] = path

    bundle_path = output_dir / f"{input_file.stem}_docs.zip"
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, p in artifacts.items():
            z.write(p, arcname=name)

    return {"ok": True, "bundle": str(bundle_path), "files": [str(p) for p in artifacts.values()]}

if __name__ == "__main__":
    import json
    print(json.dumps(run(input_file=Path("specs/demo_atomic.yaml")), indent=2))