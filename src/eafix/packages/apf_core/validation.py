from __future__ import annotations

import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Set
from .models import ProcessFlow, Step

def load_registries(root: Path) -> Tuple[Set[str], Set[str]]:
    actions = yaml.safe_load((root / "registries" / "actions.yaml").read_text(encoding="utf-8"))
    actors = yaml.safe_load((root / "registries" / "actors.yaml").read_text(encoding="utf-8"))
    action_ids = {a["id"] for a in actions.get("actions", [])}
    actor_ids = {a["id"] for a in actors.get("actors", [])}
    return action_ids, actor_ids

def validate_flow(flow: ProcessFlow, root: Path) -> List[dict]:
    """
    Basic semantic checks using registries; returns diagnostics list.
    """
    diags: List[dict] = []
    action_ids, actor_ids = load_registries(root)

    seen = set()
    for s in flow.steps:
        if s.id in seen:
            diags.append({"severity": "ERROR", "code": "APF0002", "message": f"Duplicate step id {s.id}", "location": {"step_id": s.id}})
        seen.add(s.id)
        if s.actor not in actor_ids:
            diags.append({"severity": "ERROR", "code": "APF0100", "message": f"Unknown actor '{s.actor}'", "location": {"step_id": s.id}})
        if s.action not in action_ids:
            diags.append({"severity": "ERROR", "code": "APF0101", "message": f"Unknown action '{s.action}'", "location": {"step_id": s.id}})

    idset = {s.id for s in flow.steps}
    for s in flow.steps:
        for n in s.next or []:
            if n not in idset:
                diags.append({"severity": "ERROR", "code": "APF0200", "message": f"Broken reference: {s.id} -> {n}", "location": {"step_id": s.id}})

    # Unreachable detection: any step not first and not referenced by prev steps
    referenced = set()
    for s in flow.steps:
        for n in s.next or []:
            referenced.add(n)
    if flow.steps:
        reachable = {flow.steps[0].id} | referenced
        for s in flow.steps[1:]:
            if s.id not in reachable:
                diags.append({"severity": "WARN", "code": "APF0300", "message": f"Unreachable step {s.id}", "location": {"step_id": s.id}})

    return diags
