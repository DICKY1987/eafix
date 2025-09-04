BU Document Set — Project Knowledge

Consolidated, implementation‑ready documents in the same style as your BU_* examples. Each section corresponds to a major subsystem/file set in the project knowledge. Content is aligned to YAML‑as‑Source‑of‑Truth and deterministic exporters.

Core Foundation & Models
Overview

Essential utilities (config, paths, logging/errors) and the canonical data models (ProcessFlow, AtomicStep, Branch) with schema+semantic validation.

Files & Roles

packages/apf_common/ — logging, errors, config loader/merger, path helpers

packages/apf_core/models/ids.py — StepKey primitives (parse/format/compare)

packages/apf_core/models/step.py — AtomicStep (Pydantic)

packages/apf_core/models/branch.py — decision nodes/guards/merges

packages/apf_core/models/process_flow.py — ProcessFlow aggregate + invariants

packages/apf_core/validation/{schema_loader,diagnostics,validator}.py — schema resolution, diagnostic formatters, semantic checks

Key Responsibilities

IDs/StepKey: decimal ordering with midpoint insertions; canonical precision at rest

Schema Loader: $ref resolution, caching; draft control

Validator: schema→semantic pipeline; acyclicity; unique IDs; exhaustive branches

Diagnostics: severity (ERROR/WARN/INFO), stable codes, precise locations

Contracts & Examples
# Parse/compare StepKeys
StepKey.parse('1.001') < StepKey.parse('1.002')


# Validate a flow
problems = validate_process(flow)
assert not any(p.severity=='ERROR' for p in problems)
Cross‑Cutting

Reads registries for enums (actors/actions)

Exporters/Editors depend on models; all applications are thin wrappers

Import/Export Engine
Overview

Bi‑directional conversion between YAML↔human‑readable (Markdown) and draw.io XML; JSON/YAML emitters for services.

Structure

Importers: prose_importer.py, yaml_importer.py

Exporters: markdown_exporter.py, drawio_exporter.py, json_exporter.py

Registry: __init__.py modules register capabilities with the engine

Responsibilities

Prose→YAML: map headings→steps, bullets→substeps; apply prose_rules.yaml; WARN on ambiguities with suggestions

YAML Import: load, validate against atomic schema; resolve $includes

Markdown Export: one‑line‑per‑step + branch cues; deterministic ordering

draw.io Export: stable geometry keyed by StepKey; layout presets; swimlanes by actor

JSON Export: normalized machine‑friendly representation for APIs

Commands
apf export spec.yaml --format=md,drawio,json --output-dir=derived/
Determinism Rules

Same YAML → byte‑identical artifacts (exclude timestamps/volatile fields)

Stable IDs/geometry for diff‑friendly diagrams

Sequencing & Editing
Overview

Decimal StepKey management (insert/renumber) and programmatic edit application via scripts with transactions and renumber maps.

Components

step_key.py — midpoint generation, precision control

sequencer.py — apply inserts/renumber; emit renumber map old→new

editor.py — atomic YAML edits; undo/redo hooks

edit_script.py — DSL/JSON ops: insert/update/delete/move/finalize

API Sketch
# Insert after 1.001 → auto‑midpoint (e.g., 1.0015)
seq.insert_after(flow, '1.001', new_step)
# Finalize to canonical precision (default 3)
seq.finalize(flow, precision=3)
Invariants

No duplicates; strictly increasing order; renumber map must be applied atomically under a transaction

Runtime & Security
Overview

Plugin runtime with manifest loader, sandboxing, and deny‑by‑default security policy (filesystem/network/data‑class permissions).

Key Files

huey_core/manifest.py — parse plugin.yaml, semver compat, capability map

huey_core/executor.py — run with timeouts, resource limits, recovery hooks, redaction

huey_core/policy.py — IO/network policy enforcement

Requirements

Manifests: must validate against schemas/plugin.manifest.schema.json

Least‑Privilege: CI fails if over‑permissive

Audit Trails: every execution emits structured events with run_id

Tests

Permission denial tests (attempt forbidden IO → expect failure)

Manifest schema conformance

Orchestration
Overview

Coordinator that schedules jobs, manages run state machines, and fans out/in across plugins; idempotent, retryable, resumable.

Modules

state.py — run/phase transitions; resumability

jobs.py — job units (import, validate, export); retry/backoff

coordinator.py — build execution DAGs, collect artifacts, enforce unique targets

Principles

Jobs pure w.r.t. inputs; safe to replay

Debounced watch events; bounded concurrency; clean shutdown

Recovery & State Management
Overview

Snapshots, transactions, audit logging, and documentation state store for autosave/restore and compliance.

Components

snapshot.py — content‑addressed storage; diffs

transaction.py — begin/commit/rollback; integrates with orchestrator/editor

audit_log.py — append‑only events; integrity checks

documentation_state.py — version graph, autosave, migrations, restore points

Guarantees

All‑or‑nothing writes for renumber/write‑backs

Restorable versions by version_id; correlated by run_id

Process Library & Parser
Process Library

DB Layer (db.py) — SQLite with FTS; referential integrity

Migrations (migrations.py) — schema versions; seed data

Templates (templates.py) — resolve template_id@version; parameter substitution; provenance

Parser (Structured Docs → Models)

structured_document.py — map headings/tables/lists to steps/branches; attach metadata

streaming.py — incremental, bounded‑memory parsing; progressive diagnostics; resumable offsets

Library Contracts

Template IDs: lib.<domain>.<name>@<semver>; unpinned resolves latest compatible

First‑Party Plugins
Manifests & Capabilities

Engine (plugins/atomic_process_engine) — import→validate→export pipeline

Step Sequencer — seq.insert, seq.renumber

Process Standardizer — normalize prose via prose_rules.yaml

Diagram Generator — wrap draw.io exporter (+ Mermaid optional)

Validation Engine — advanced cross‑file/security checks

Documentation — bundle MD/diagrams/assets into zip/PDF

Rules

IDs: lowercase dot‑separated <org>.<package>.<name>

Compat: declare apf_core semver ranges; executor refuses mismatches

Applications (Thin Wrappers)
CLI (apps/cli/apf)

Subcommands: export, validate, seq, watch

Global flags: --verbose, --config, --format=...

HTTP Service (FastAPI)

Endpoints: /validate, /export, /decide, /health, /docs

Streams diagnostics; returns artifacts

Desktop (PySide6)

Dockable shell; YAML editor with live validation; Problems panel; StepKey helpers; diff view

Bootstrap & Contracts
Purpose

Define “valid” first: schemas, registries, configs, and CI/tooling.

Contents

schemas/atomic_process.schema.json — ProcessFlow/Step/Branch shapes; StepKey numeric formats; enums from registries

schemas/plugin.manifest.schema.json — plugin contracts

schemas/library.schema.json — template contracts

Registries — actors.yaml, actions.yaml, naming.yaml, prose_rules.yaml

Examples — example_files/demo_atomic.yaml, hello_world.yaml

Tooling — pyproject.toml, .pre-commit-config.yaml, .github/workflows/ci.yml

Diagnostics Schema & Testing (Recap)
JSON Schema Highlights

Array of Diagnostic; required: severity, code, message

Location supports file, line/column, json_pointer, optional step_id (^\d+(\.\d{3,})?$)

Stable code pattern: APF####

Tests

Registry shape/duplicate checks

Diagnostics schema conformance + JSON round‑trip stability

Change Request (Edit Script) Schema
Purpose

Contract for machine‑applied change requests (CRs) against the master YAML with auditability and guardrails.

Key Fields

Top‑level: change_id (CR-YYYYMMDD-HHMMSS-slug), title, author, created_utc, target_file, optional rationale, apf_schema_version

Preconditions: expected_master_sha256, expected_stepkey_precision

ops[]: sequence of operations; each has op_id, op (enum), and op‑specific fields

Signing (optional): sha256_of_ops, gpg_fingerprint, signature_detached_ascii_armor

Op Types

insert_step_after, insert_step_before, update_field, delete_step, move_step, set_metadata, set_registry_item, finalize_renumber

Validation Snippet
python -m jsonschema schemas/apf_edit_script.schema.json change_requests/CR-*.json
Apply Stub (apf_apply_stub.py)
What it Does (Now)

Lints CR files for required fields

Computes/compares expected_master_sha256

Supports dry‑run summary of ops

Writes an audit log folder audit/<change_id>/apply.log

Usage
python apf_apply_stub.py --lint-cr "change_requests/*.yaml"
python apf_apply_stub.py --apply CR-20250822-123000-demo.yaml --dry-run
Next Steps to Productionize

Wire to real sequencer/editor operations

Wrap in transaction + snapshot; run validators; emit renumber map

Enforce policy: only allowed fields/ops; signature verification (optional)

Monorepo Build Order & Rules (Recap)
Dependency‑Aware Order

Bootstrap & Contracts → 2) Common Infra → 3) Core Models/Validation → 4) Sequencing → 5) Import/Export → 6) Plugin Backbone → 7) Security/Recovery/State → 8) Orchestration → 9) Process Library → 10) Parser → 11) Plugins → 12) Apps → 13) Tests/Examples/Docs

Ubiquitous Language (Selected)

AtomicStep, ProcessFlow, Branch, StepKey, Renumber Map, Diagnostic, Importer/Exporter, Plugin/Capability/Manifest, Orchestrator/Job/Run, Snapshot/Transaction/Audit Log, State Store/Documentation State, Streaming Parser, Watch Loop, Artifact

Must‑Follow Rules

YAML is source of truth; MD/Draw.io/JSON are derived

Determinism: same input → identical outputs

Branches must be exhaustive or provide a default path

Plugin security: deny‑by‑default; manifests validated in CI

All sequencing edits produce a renumber map and commit under a transaction

Appendix — CLI Cheatsheet
# Validate spec → diagnostics (table)
apf validate specs/demo_atomic.yaml --format=table


# Export all artifacts (MD + draw.io + JSON)
apf export specs/demo_atomic.yaml --format=md,drawio,json --output-dir=derived/


# Insert and finalize numbering
apf seq insert specs/demo_atomic.yaml --after=1.001 --backup
apf seq renumber specs/demo_atomic.yaml --start=1.001 --increment=0.001


# Watch and auto‑refresh artifacts on change
apf watch specs/ --patterns "*.yaml" --debounce=500ms

Done! I created a consolidated BU-style document set covering every subsystem from your project knowledge (core models, import/export, sequencing, runtime/security, orchestration, recovery/state, process library & parser, plugins, apps, bootstrap/contracts, diagnostics, and the CR schema + apply stub). You’ll find it in the canvas titled “BU Document Set All”.

Source mapping for what I used (so you can trace each section to its origin): core foundation/models , import/export engine , sequencing & editing , runtime & security , orchestration , recovery & state , process library & parser , first-party plugins , applications (recap) , diagnostics schema/testing (recap) , tests & rules (alignment) , bootstrap & contracts , change-request schema JSON and apply stub , and the deep build-order doc for cross-checks .