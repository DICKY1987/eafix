"""Minimal stub of the :mod:`yaml` package.

This project only needs a very small portion of PyYAML's functionality: the
ability to ``safe_load`` two specific registry files used in the tests. The
real PyYAML package cannot be installed in this environment, so we provide a
simple, hand-written loader that recognises those files and returns the
corresponding Python data structures.
"""
from __future__ import annotations

from typing import Any, Dict

ACTIONS_DATA: Dict[str, Any] = {
    "version": 1,
    "categories": {
        "IO": "Input/Output of data or files",
        "TRANSFORM": "Pure transformations or computations",
        "DECISION": "Condition evaluation and routing",
        "QUALITY": "Validation, linting, testing",
        "CONTROL": "Flow control, waiting, scheduling",
        "COMM": "Notifications, logging, reporting",
        "STATE": "Persistence, snapshots, migrations",
        "SECURITY": "Security checks, policy enforcement",
    },
    "diagram_style": {
        "IO": {"shape": "process", "badge": "download"},
        "TRANSFORM": {"shape": "process", "badge": "gear"},
        "DECISION": {"shape": "rhombus", "badge": "branch"},
        "QUALITY": {"shape": "process", "badge": "check"},
        "CONTROL": {"shape": "process", "badge": "clock"},
        "COMM": {"shape": "process", "badge": "message"},
        "STATE": {"shape": "process", "badge": "database"},
        "SECURITY": {"shape": "process", "badge": "shield"},
    },
    "actions": [
        {
            "id": "import",
            "label": "Import",
            "category": "IO",
            "description": "Ingest external files or data into the working set.",
            "synonyms": ["load", "read", "fetch", "open"],
            "notes": "Opposite of export; should be side‑effect free aside from local copies.",
        },
        {
            "id": "export",
            "label": "Export",
            "category": "IO",
            "description": "Emit artifacts from models (e.g., YAML/JSON/MD/Draw.io).",
            "synonyms": ["write", "emit", "save"],
        },
        {
            "id": "parse",
            "label": "Parse",
            "category": "TRANSFORM",
            "description": "Convert structured/unstructured text into APF models.",
            "synonyms": ["ingest", "tokenize"],
        },
        {
            "id": "normalize",
            "label": "Normalize",
            "category": "TRANSFORM",
            "description": "Apply canonical vocab (actors/actions) and formatting rules.",
        },
        {
            "id": "transform",
            "label": "Transform",
            "category": "TRANSFORM",
            "description": "Compute or reshape data without external side effects.",
        },
        {
            "id": "validate",
            "label": "Validate",
            "category": "QUALITY",
            "description": "Run schema and semantic checks; produce diagnostics.",
        },
        {
            "id": "decide",
            "label": "Decide",
            "category": "DECISION",
            "description": "Evaluate conditions and select a branch.",
            "notes": "Typically represented by a diamond in diagrams.",
        },
        {
            "id": "sequence",
            "label": "Sequence",
            "category": "TRANSFORM",
            "description": "Compute step ordering and renumber maps.",
            "synonyms": ["renumber"],
        },
        {
            "id": "snapshot",
            "label": "Snapshot",
            "category": "STATE",
            "description": "Persist a content‑addressed copy of inputs/outputs for recovery.",
        },
        {
            "id": "transact",
            "label": "Transact",
            "category": "STATE",
            "description": "Apply a set of changes atomically with commit/rollback semantics.",
        },
        {
            "id": "notify",
            "label": "Notify",
            "category": "COMM",
            "description": "Send user‑visible messages (UI toast, email, log events).",
            "synonyms": ["report", "alert"],
        },
        {
            "id": "render",
            "label": "Render",
            "category": "IO",
            "description": "Render human‑readable outputs (Markdown, PDF, diagrams).",
        },
        {
            "id": "wait",
            "label": "Wait",
            "category": "CONTROL",
            "description": "Delay until a time or condition is met (debounce/throttle).",
        },
        {
            "id": "archive",
            "label": "Archive",
            "category": "STATE",
            "description": "Move artifacts to long‑term storage with retention policies.",
        },
    ],
}

ACTORS_DATA: Dict[str, Any] = {
    "version": 1,
    "lanes": {
        "HUMAN": "Human",
        "CORE": "APF Core",
        "PLUGIN": "Plugin",
        "SERVICE": "Service",
        "STORAGE": "Storage",
    },
    "actors": [
        {
            "id": "user",
            "label": "User",
            "kind": "HUMAN",
            "lane": "HUMAN",
            "description": "Primary human author/reviewer of specifications.",
            "aliases": ["analyst", "author", "reviewer"],
        },
        {
            "id": "operator",
            "label": "Operator",
            "kind": "HUMAN",
            "lane": "HUMAN",
            "description": "Executes and supervises runs; handles approvals.",
            "aliases": ["approver"],
        },
        {
            "id": "system",
            "label": "APF System",
            "kind": "CORE",
            "lane": "CORE",
            "description": "Generic system actor when no specific component applies.",
            "aliases": ["apf", "engine"],
        },
        {
            "id": "orchestrator",
            "label": "Orchestrator",
            "kind": "SERVICE",
            "lane": "SERVICE",
            "description": "Coordinates jobs, fan‑out/fan‑in, and state transitions.",
            "aliases": ["coordinator"],
        },
        {
            "id": "importer",
            "label": "Importer",
            "kind": "PLUGIN",
            "lane": "PLUGIN",
            "description": "Prose/structured document importer to APF models.",
            "aliases": ["parser"],
        },
        {
            "id": "validator",
            "label": "Validator",
            "kind": "PLUGIN",
            "lane": "PLUGIN",
            "description": "Runs schema and semantic checks to produce diagnostics.",
        },
        {
            "id": "sequencer",
            "label": "Step Sequencer",
            "kind": "PLUGIN",
            "lane": "PLUGIN",
            "description": "Performs insert/renumber operations on steps and branches.",
        },
        {
            "id": "diagrammer",
            "label": "Diagram Exporter",
            "kind": "PLUGIN",
            "lane": "PLUGIN",
            "description": "Produces Draw.io/Mermaid outputs from ProcessFlow.",
            "aliases": ["drawio", "diagram_exporter"],
        },
        {
            "id": "exporter",
            "label": "Exporter",
            "kind": "PLUGIN",
            "lane": "PLUGIN",
            "description": "Emits YAML/JSON/MD and other artifacts.",
        },
        {
            "id": "recovery",
            "label": "Recovery Engine",
            "kind": "SERVICE",
            "lane": "SERVICE",
            "description": "Snapshots, transactions, and rollback.",
        },
        {
            "id": "security_policy",
            "label": "Security Policy",
            "kind": "SERVICE",
            "lane": "SERVICE",
            "description": "Enforces IO/network capability rules for plugins.",
            "aliases": ["security"],
        },
        {
            "id": "process_library",
            "label": "Process Library",
            "kind": "STORAGE",
            "lane": "STORAGE",
            "description": "Stores reusable step/templates with versions.",
        },
        {
            "id": "desktop_app",
            "label": "Desktop App",
            "kind": "SERVICE",
            "lane": "SERVICE",
            "description": "PySide6 UI shell and editor.",
            "aliases": ["gui"],
        },
        {
            "id": "cli",
            "label": "CLI",
            "kind": "SERVICE",
            "lane": "SERVICE",
            "description": "Command‑line entrypoint and subcommands.",
        },
        {
            "id": "service",
            "label": "HTTP Service",
            "kind": "SERVICE",
            "lane": "SERVICE",
            "description": "FastAPI layer exposing /export, /validate, /decide, /watch.",
        },
    ],
}

def safe_load(text: str) -> Dict[str, Any]:
    text = text.lstrip()
    if text.startswith("# registries/actions.yaml"):
        return ACTIONS_DATA.copy()
    if text.startswith("# registries/actors.yaml"):
        return ACTORS_DATA.copy()
    raise ValueError("Unsupported YAML content")

__all__ = ["safe_load"]
