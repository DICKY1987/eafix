1) apf_common (logging, config, paths, errors)

These are tiny but foundational; wire first.

packages/apf_common/src/apf_common/__init__.py

from .logging import get_logger
from .errors import ValidationError, SchemaError, PluginError, OrchestrationError
from .config import load_config, AppConfig
from .paths import RepoPaths

__all__ = [
    "get_logger", "ValidationError", "SchemaError", "PluginError", "OrchestrationError",
    "load_config", "AppConfig", "RepoPaths",
]


packages/apf_common/src/apf_common/errors.py

class SchemaError(Exception): ...
class ValidationError(Exception): ...
class PluginError(Exception): ...
class OrchestrationError(Exception): ...


packages/apf_common/src/apf_common/logging.py

import logging, json, os, sys, time
def get_logger(component: str, run_id: str | None = None) -> logging.Logger:
    logger = logging.getLogger(component); logger.setLevel(logging.INFO)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(h)
    def _emit(level: int, msg: str, **kw):
        rec = {"ts": time.time(), "component": component, "run_id": run_id, "msg": msg} | kw
        logger.log(level, json.dumps(rec, ensure_ascii=False))
    logger.json = _emit  # type: ignore[attr-defined]
    return logger


packages/apf_common/src/apf_common/config.py

from dataclasses import dataclass
from pathlib import Path
import os, yaml

@dataclass
class AppConfig:
    registries_dir: Path
    defaults_yaml: Path
    stepkey_precision: int = 3

def load_config(repo_root: Path | None = None) -> AppConfig:
    root = repo_root or Path.cwd()
    user_cfg = Path.home() / ".huey-apf" / "config.yaml"
    defaults = root / "config" / "defaults.yaml"
    cfg = {"stepkey_precision": 3}
    if defaults.exists(): cfg |= yaml.safe_load(defaults.read_text()) or {}
    if user_cfg.exists(): cfg |= yaml.safe_load(user_cfg.read_text()) or {}
    return AppConfig(registries_dir=root / "registries", defaults_yaml=defaults, **cfg)


packages/apf_common/src/apf_common/paths.py

from dataclasses import dataclass
from pathlib import Path

@dataclass
class RepoPaths:
    root: Path
    derived: Path
    schemas: Path
    registries: Path

    @classmethod
    def discover(cls, start: Path | None = None) -> "RepoPaths":
        cur = (start or Path.cwd()).resolve()
        for p in [cur, *cur.parents]:
            if (p / "pyproject.toml").exists():
                return cls(root=p, derived=p / "derived", schemas=p / "schemas", registries=p / "registries")
        raise RuntimeError("Repo root not found (missing pyproject.toml)")


These align to “Core Foundation & Models → apf_common.”

2) apf_core (IDs, models, validation)

Implements StepKey + Pydantic models + schema/semantic validation entrypoints.

packages/apf_core/src/apf_core/models/ids.py

from dataclasses import dataclass

@dataclass(frozen=True, order=True)
class StepKey:
    major: int
    frac: int
    precision: int = 3

    @classmethod
    def parse(cls, s: str) -> "StepKey":
        if "." not in s: return cls(int(s), 0, 0)
        major, frac = s.split(".", 1)
        return cls(int(major), int(frac), len(frac))

    def __str__(self) -> str:
        return f"{self.major}.{self.frac:0{self.precision}d}" if self.precision else str(self.major)

    def midpoint(self, other: "StepKey") -> "StepKey":
        assert self.major == other.major, "midpoint across majors not allowed"
        width = max(self.precision, other.precision) + 1
        a = int(f"{self.frac:0{width}d}"); b = int(f"{other.frac:0{width}d}")
        mid = (a + b) // 2
        return StepKey(self.major, mid, width)

    def with_precision(self, precision: int) -> "StepKey":
        return StepKey(self.major, int(round(self.frac / (10 ** (self.precision - precision)))), precision)


packages/apf_core/src/apf_core/models/step.py

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class AtomicStep(BaseModel):
    step_id: str = Field(..., pattern=r"^\d+(\.\d{3,})?$")
    actor: str
    action: str
    inputs: List[str] = []
    outputs: List[str] = []
    notes: Optional[str] = None
    meta: Dict[str, Any] = {}


packages/apf_core/src/apf_core/models/branch.py

from pydantic import BaseModel
from typing import List

class Branch(BaseModel):
    from_step: str
    guards: List[dict]  # [{"label": "ok", "to": "2.001", "expr": "x>0"}, ...]
    merge_to: str | None = None


packages/apf_core/src/apf_core/models/process_flow.py

from pydantic import BaseModel, Field, root_validator
from typing import List
from .step import AtomicStep
from .branch import Branch

class ProcessFlow(BaseModel):
    title: str
    steps: List[AtomicStep] = Field(default_factory=list)
    branches: List[Branch] = Field(default_factory=list)

    @root_validator
    def _invariants(cls, values):
        ids = [s.step_id for s in values.get("steps", [])]
        assert len(ids) == len(set(ids)), "Duplicate StepKey detected"
        return values


packages/apf_core/src/apf_core/validation/schema_loader.py

import json, jsonschema
from pathlib import Path

class SchemaLoader:
    def __init__(self, base: Path): self.base = base
    def load(self, name: str) -> dict:
        path = (self.base / name).resolve()
        return json.loads(path.read_text(encoding="utf-8"))
    def validate(self, schema_name: str, instance: dict | list) -> None:
        schema = self.load(schema_name)
        jsonschema.Draft202012Validator(schema).validate(instance)


packages/apf_core/src/apf_core/validation/validator.py

from typing import Iterable, List, Dict, Any
from .schema_loader import SchemaLoader

class Diagnostic(dict): ...  # shape matches diagnostics schema

class Validator:
    def __init__(self, schemas, registries):
        self.schemas, self.registries = schemas, registries

    def validate_schema(self, flow_doc: Dict[str, Any]) -> List[Diagnostic]:
        try:
            self.schemas.validate("atomic_process.schema.json", flow_doc)
            return []
        except Exception as e:
            return [self.error("APF0000", f"Schema error: {e}")]

    def validate_semantics(self, flow_doc: Dict[str, Any]) -> List[Diagnostic]:
        diags: List[Diagnostic] = []
        steps = flow_doc.get("steps", [])
        ids = [s["step_id"] for s in steps]
        if len(ids) != len(set(ids)):
            diags.append(self.error("APF0100", "Duplicate StepKey detected"))
        # Unknown actor/action
        actors = {a["id"] for a in self.registries["actors"]["actors"]}
        actions = {a["id"] for a in self.registries["actions"]["actions"]}
        for s in steps:
            if s["actor"] not in actors: diags.append(self.error("APF0001", f"Unknown actor '{s['actor']}'"))
            if s["action"] not in actions: diags.append(self.error("APF0002", f"Unknown action '{s['action']}'"))
        return diags

    @staticmethod
    def error(code: str, message: str) -> Diagnostic:
        return {"severity":"ERROR","code":code,"message":message}


Matches the “Core Model + Validation” responsibilities.

3) sequencing & editing

Provides midpoint insertion, canonical renumber, and an edit-script driver.

packages/sequencing/src/sequencing/step_key.py

from apf_core.models.ids import StepKey

def insert_after(curr: StepKey, nxt: StepKey | None) -> StepKey:
    return curr.midpoint(nxt) if nxt else StepKey(curr.major, curr.frac + 1, curr.precision)

def canonicalize(key: StepKey, precision: int) -> StepKey:
    return key.with_precision(precision)


packages/sequencing/src/sequencing/sequencer.py

from typing import List, Dict
from apf_core.models.ids import StepKey
from .step_key import insert_after, canonicalize

def renumber(step_ids: List[str], precision: int = 3) -> Dict[str, str]:
    """Return old->new StepKey map with canonical precision."""
    old = [StepKey.parse(s) for s in step_ids]
    new = [canonicalize(k, precision) for k in old]
    return {str(o): str(n) for o, n in zip(old, new)}

def insert_between(prev_id: str, next_id: str | None, precision: int) -> str:
    k = insert_after(StepKey.parse(prev_id), StepKey.parse(next_id) if next_id else None)
    return str(canonicalize(k, max(k.precision, precision)))


packages/editing/src/editing/editor.py

from copy import deepcopy

class YAMLEditor:
    def __init__(self, doc: dict): self.doc = deepcopy(doc)

    def update_field(self, step_id: str, field: str, value):
        for s in self.doc.get("steps", []):
            if s["step_id"] == step_id:
                s[field] = value; return True
        return False


packages/editing/src/editing/edit_script.py

import json, hashlib
from .editor import YAMLEditor

def apply_edit_script(master: dict, cr: dict) -> dict:
    ed = YAMLEditor(master)
    for op in cr["ops"]:
        match op["op"]:
            case "update_field":
                ed.update_field(op["target_step"], op["field"], op["value"])
            # TODO: insert_step_after, delete_step, move_step, finalize_renumber
            case _:
                raise ValueError(f"Unknown op {op['op']}")
    return ed.doc


Implements the “insert/renumber” and edit-script hooks.

4) import/export engine

Importer registry + Markdown/JSON/Draw.io exporters with stable output.

packages/import_export/src/import_export/exporters/__init__.py

from typing import Protocol

class Exporter(Protocol):
    def export(self, flow: dict) -> str: ...

REGISTRY = {}

def register(fmt: str, exporter: Exporter) -> None:
    REGISTRY[fmt] = exporter

def get(fmt: str) -> Exporter:
    return REGISTRY[fmt]


.../exporters/markdown_exporter.py

from . import register
def _one_line(step: dict) -> str:
    io = " — ".join(filter(None, [
        f"{step['actor']}", f"{step['action']}",
        ("; ".join(step.get("inputs", [])) + " → " + "; ".join(step.get("outputs", []))) if step.get("inputs") or step.get("outputs") else None
    ]))
    return f"{step['step_id']}. {io}"
class MarkdownExporter:
    def export(self, flow: dict) -> str:
        lines = [f"# {flow.get('title','Process')}", ""]
        lines += [_one_line(s) for s in flow.get("steps", [])]
        return "\n".join(lines)
register("md", MarkdownExporter())


.../exporters/json_exporter.py

import json
from . import register
class JSONExporter:
    def export(self, flow: dict) -> str:
        return json.dumps(flow, indent=2, separators=(",", ": "))
register("json", JSONExporter())


.../exporters/drawio_exporter.py

from . import register

TEMPLATE = """<mxfile><diagram name="Process"><mxGraphModel><root>
  <mxCell id="0"/><mxCell id="1" parent="0"/>
  {nodes}
  {edges}
</root></mxGraphModel></diagram></mxfile>"""

def _node_xml(i, step): 
    x = 80 + (i % 4) * 220; y = 80 + (i // 4) * 120
    return f'<mxCell id="{step["step_id"]}" value="{step["step_id"]} {step["actor"]}:{step["action"]}" style="rounded=1;whiteSpace=wrap;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="200" height="60" as="geometry"/></mxCell>'

def _edge_xml(frm, to): 
    return f'<mxCell id="{frm}->{to}" edge="1" source="{frm}" target="{to}" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>'

class DrawioExporter:
    def export(self, flow: dict) -> str:
        nodes = "\n  ".join(_node_xml(i,s) for i,s in enumerate(flow.get("steps", [])))
        # TODO: real graph edges; for now, connect sequentially:
        ids = [s["step_id"] for s in flow.get("steps", [])]
        edges = "\n  ".join(_edge_xml(a,b) for a,b in zip(ids, ids[1:]))
        return TEMPLATE.format(nodes=nodes, edges=edges)
register("drawio", DrawioExporter())


packages/import_export/src/import_export/importers/yaml_importer.py

import yaml
from apf_core.validation.schema_loader import SchemaLoader

def load_yaml_and_validate(path: str, loader: SchemaLoader) -> dict:
    data = yaml.safe_load(open(path, "r", encoding="utf-8"))
    loader.validate("atomic_process.schema.json", data)
    return data


These mirror the Import/Export responsibilities (MD one-liner, JSON, draw.io XML).

5) Plugin backbone (manifest, registry, executor)

Minimal plug-in API + safe execution shim.

packages/huey_core/src/huey_core/plugin_base.py

from typing import Protocol, Any

class Plugin(Protocol):
    id: str
    def init(self, ctx: dict) -> None: ...
    def execute(self, **kwargs) -> Any: ...
    def shutdown(self) -> None: ...


packages/huey_core/src/huey_core/manifest.py

import yaml
def load_manifest(path: str) -> dict:
    return yaml.safe_load(open(path, "r", encoding="utf-8"))


packages/huey_core/src/huey_core/registry.py

from importlib import import_module
from pathlib import Path
from .manifest import load_manifest

def load_plugin(manifest_path: str):
    m = load_manifest(manifest_path)
    mod = import_module(m["entry_point"]["module"])
    cls = getattr(mod, m["entry_point"]["class"])
    plugin = cls()
    plugin.id = m["id"]
    return plugin, m


packages/huey_core/src/huey_core/executor.py

import contextlib, tempfile, shutil, time
from typing import Any

def run_plugin(plugin, manifest: dict, **kwargs) -> Any:
    with tempfile.TemporaryDirectory() as ws:
        ctx = {"workspace": ws, "policy": manifest.get("io_policies", {})}
        plugin.init(ctx)
        try:
            return plugin.execute(**kwargs)
        finally:
            with contextlib.suppress(Exception): plugin.shutdown()


Matches “First-Party Plugins (compose features)” and is enough to run your plugin.py files.

Example engine plugin skeleton

plugins/atomic_process_engine/plugin.py

from apf_core.validation.validator import Validator
from apf_core.validation.schema_loader import SchemaLoader
from import_export.exporters import get as get_exporter
import yaml, json
from pathlib import Path

class AtomicProcessEngine:
    id = "apf.atomic_process_engine"

    def init(self, ctx: dict): self.ctx = ctx
    def execute(self, target_file: str, registries: dict, outputs: list[str] = ["md","json","drawio"]):
        loader = SchemaLoader(Path("schemas"))
        flow = yaml.safe_load(open(target_file, "r", encoding="utf-8"))
        diags = Validator(loader, registries).validate_semantics(flow)
        if any(d["severity"] == "ERROR" for d in diags):
            return {"status":"error","diagnostics":diags}
        artifacts = {fmt: get_exporter(fmt).export(flow) for fmt in outputs}
        return {"status":"ok","diagnostics":diags,"artifacts":artifacts}
    def shutdown(self): ...


Matches the engine’s “import→validate→export” orchestration.

6) Security & recovery (policy, snapshot, transaction, audit)

Bare-minimum scaffolds to enforce least-privilege and audit.

packages/security/src/security/policy.py

def check_io_policy(policy: dict, path: str, mode: str) -> bool:
    # TODO: implement glob restrictions; deny by default
    return True


packages/recovery/src/recovery/snapshot.py

import hashlib, json
def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
def snapshot_bytes(path: str, data: bytes) -> str:
    h = content_hash(data); open(path, "wb").write(data); return h


packages/recovery/src/recovery/transaction.py

from contextlib import contextmanager
@contextmanager
def transaction():
    try: yield
    except Exception:  # TODO: rollback hooks
        raise


packages/recovery/src/recovery/audit_log.py

import json, time, os
def audit_append(path: str, event: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), **event}) + "\n")


Mirrors “Recovery & State Management” building blocks.

7) Orchestration (jobs, state, coordinator)

Simple coordinator that can back your CLI watch loop.

packages/orchestration/src/orchestration/jobs.py

from dataclasses import dataclass
@dataclass
class Job: name: str; args: dict


packages/orchestration/src/orchestration/state.py

class RunState:
    def __init__(self): self.events = []
    def record(self, ev: str, **kw): self.events.append((ev, kw))


packages/orchestration/src/orchestration/coordinator.py

from .jobs import Job
from huey_core.executor import run_plugin

class Coordinator:
    def __init__(self, registry): self.registry = registry
    def run(self, job: Job):
        plugin, manifest = self.registry.resolve(job.name)
        return run_plugin(plugin, manifest, **job.args)

8) Process Library (DB + templates)

Provide the interfaces; fill out migrations later.

packages/process_library/src/process_library/templates.py

def resolve_template(id_version: str, params: dict) -> dict:
    """Resolve lib.<domain>.<name>@<semver> and apply params -> step dict."""
    # TODO: look up from SQLite; for now return parametrized stub
    return {"actor": params.get("actor","system"), "action": params["action"], "inputs": params.get("inputs",[]), "outputs": params.get("outputs",[])}

9) Parser (structured docs → models)

Deterministic, table/list aware; streaming stub shown too.

packages/apf_parser/src/apf_parser/structured_document.py

from typing import Iterable, Dict

def parse_markdown(md_lines: Iterable[str]) -> Dict:
    # TODO: implement headings→sections, bullets→steps
    return {"title": "Imported Process", "steps": []}


packages/apf_parser/src/apf_parser/streaming.py

def stream_parse(fp, chunk_size=65536):
    while (chunk := fp.read(chunk_size)):
        yield {"severity":"INFO","code":"APF9999","message":"chunk processed","data":{"size":len(chunk)}}

10) Apps (CLI, service, desktop)

Wire CLI subcommands and a tiny FastAPI surface; desktop shells are minimal but correct.

CLI

apps/cli/apf/__main__.py

import typer
from .commands import export as cmd_export, validate as cmd_validate, seq as cmd_seq
app = typer.Typer()
app.command("export")(cmd_export.main)
app.command("validate")(cmd_validate.main)
app.command("seq")(cmd_seq.main)
if __name__ == "__main__": app()


apps/cli/apf/commands/export.py

import typer, yaml, json
from import_export.exporters import get as get_exporter

def main(file: str, fmt: str = "md"):
    flow = yaml.safe_load(open(file, "r", encoding="utf-8"))
    print(get_exporter(fmt).export(flow))


apps/cli/apf/commands/validate.py

import typer, yaml
from pathlib import Path
from apf_core.validation.validator import Validator
from apf_core.validation.schema_loader import SchemaLoader

def main(file: str):
    flow = yaml.safe_load(open(file,"r",encoding="utf-8"))
    loader = SchemaLoader(Path("schemas"))
    registries = {"actors": yaml.safe_load(open("registries/actors.yaml","r")), 
                  "actions": yaml.safe_load(open("registries/actions.yaml","r"))}
    v = Validator(loader, registries)
    diags = v.validate_schema(flow) + v.validate_semantics(flow)
    for d in diags: print(d)
    raise typer.Exit(code=1 if any(x["severity"]=="ERROR" for x in diags) else 0)


Service

apps/service/main.py

from fastapi import FastAPI
from .routes import attach_routes
def create_app() -> FastAPI:
    app = FastAPI(title="APF Service")
    attach_routes(app)
    return app


apps/service/routes.py

from fastapi import FastAPI, UploadFile
import yaml, json
from pathlib import Path
from apf_core.validation.validator import Validator
from apf_core.validation.schema_loader import SchemaLoader

def attach_routes(app: FastAPI):
    @app.post("/validate")
    async def validate(file: UploadFile):
        loader = SchemaLoader(Path("schemas"))
        doc = yaml.safe_load(await file.read())
        diags = Validator(loader, {"actors":{}, "actions":{}}).validate_semantics(doc)
        return {"diagnostics": diags}

    @app.post("/export/{fmt}")
    async def export(fmt: str, file: UploadFile):
        from import_export.exporters import get
        doc = yaml.safe_load(await file.read())
        return {"artifact": get(fmt).export(doc)}


Desktop

apps/desktop/main.py

from PySide6.QtWidgets import QApplication
from .ui_shell import MainWindow
import sys
if __name__ == "__main__":
    app = QApplication(sys.argv); w = MainWindow(); w.show(); sys.exit(app.exec())


apps/desktop/ui_shell.py

from PySide6.QtWidgets import QMainWindow, QTextEdit, QDockWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("APF Desktop")
        self.editor = QTextEdit(self); self.setCentralWidget(self.editor)
        dock = QDockWidget("Diagnostics", self); dock.setWidget(QTextEdit()); self.addDockWidget(0x1, dock)


These match your CLI/service/desktop responsibilities.

11) First-party plugin manifests

Copy + fill out per plugin.

plugins/atomic_process_engine/plugin.yaml

id: apf.atomic_process_engine
version: 0.1.0
entry_point: { module: "plugins.atomic_process_engine.plugin", class: "AtomicProcessEngine" }
capabilities: ["import.yaml", "validate", "export.md", "export.json", "export.drawio"]
io_policies: { read: ["**/*.yaml","schemas/**"], write: ["derived/**"] }
apf_core_compat: "^0.1"

12) Tests (quick wins)

Pin down StepKey math and validator errors; expand later.

tests/unit/test_step_key.py

from apf_core.models.ids import StepKey
def test_midpoint_extends_precision():
    a = StepKey.parse("1.001"); b = StepKey.parse("1.002")
    m = a.midpoint(b)
    assert str(m).startswith("1.") and m.precision > 3


tests/unit/test_validator.py

from apf_core.validation.validator import Validator
from apf_core.validation.schema_loader import SchemaLoader
from pathlib import Path

def test_unknown_actor_emits_error(tmp_path):
    flow = {"title":"x","steps":[{"step_id":"1.001","actor":"nope","action":"import"}]}
    regs = {"actors":{"actors":[]}, "actions":{"actions":[{"id":"import"}]}}
    v = Validator(SchemaLoader(Path("schemas")), regs)
    diags = v.validate_semantics(flow)
    assert any(d["code"]=="APF0001" for d in diags)