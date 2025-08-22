from __future__ import annotations
import json
from apf_core.models import ProcessFlow

def export_json(flow: ProcessFlow) -> str:
    data = {
        "meta": flow.meta,
        "steps": [{
            "id": s.id, "actor": s.actor, "action": s.action, "text": s.text, "next": s.next or []
        } for s in flow.steps]
    }
    return json.dumps(data, ensure_ascii=False, indent=2)
