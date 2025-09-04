from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
from import_export import load_yaml_flow
from import_export.loaders import dump_yaml_flow
from apf_core import StepSequencer

def _ins(flow, after: str, actor: str, action: str, text: str) -> str:
    ids = [s.id for s in flow.steps]
    seq = StepSequencer()
    new_id = seq.insert_after(ids, after)
    idx = ids.index(after) + 1
    Step = type(flow.steps[0])
    flow.steps.insert(idx, Step(id=new_id, actor=actor, action=action, text=text, next=[]))
    return new_id

def _renum(flow, start: str, increment: str) -> int:
    seq = StepSequencer()
    old_ids = [s.id for s in flow.steps]
    new_ids = seq.renumber(old_ids, start=start, increment=increment)
    id_map = dict(zip(old_ids, new_ids))
    for s in flow.steps:
        s.id = id_map[s.id]
        if s.next:
            s.next = [id_map.get(n, n) for n in s.next]
    return len(old_ids)

def run(command: str, **kwargs) -> Dict[str, Any]:
    input_file: Path = Path(kwargs.get("input_file"))
    backup: bool = bool(kwargs.get("backup", True))
    flow = load_yaml_flow(input_file)

    if command == "insert":
        new_id = _ins(flow, kwargs["after"], kwargs.get("actor","user"), kwargs.get("action","transform"), kwargs.get("text","New step"))
        if backup:
            input_file.with_suffix(".bak.yaml").write_text(input_file.read_text(encoding="utf-8"), encoding="utf-8")
        input_file.write_text(dump_yaml_flow(flow), encoding="utf-8")
        return {"ok": True, "inserted": new_id}
    elif command == "renumber":
        count = _renum(flow, kwargs.get("start","1.001"), kwargs.get("increment","0.001"))
        if backup:
            input_file.with_suffix(".bak.yaml").write_text(input_file.read_text(encoding="utf-8"), encoding="utf-8")
        input_file.write_text(dump_yaml_flow(flow), encoding="utf-8")
        return {"ok": True, "renumbered": count}
    else:
        return {"ok": False, "error": f"unknown command: {command}"}

if __name__ == "__main__":
    import json
    print(json.dumps(run("insert", input_file=Path("specs/demo_atomic.yaml"), after="1.002"), indent=2))