from __future__ import annotations
import yaml, json
from pathlib import Path
from typing import Any, Dict
from apf_core.models import ProcessFlow, Step

def load_yaml_flow(path: Path) -> ProcessFlow:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    steps = [Step(**s) for s in data.get("steps", [])]
    return ProcessFlow(meta=data.get("meta", {}), steps=steps)

def dump_yaml_flow(flow: ProcessFlow) -> str:
    data = {
        "meta": flow.meta,
        "steps": [{
            "id": s.id,
            "actor": s.actor,
            "action": s.action,
            "text": s.text,
            "next": s.next or []
        } for s in flow.steps]
    }
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
