# Tests & System Rules

> Test infrastructure and system-wide rules and invariants for the Atomic Process Framework.

## Test Structure & Organization

### Unit Tests
- **`tests/unit/test_step_key.py`** - StepKey correctness: Parse/format/compare; midpoints; ordering edge cases
- **`tests/unit/test_validator.py`** - Validation coverage: Schema violations, semantic invariants, helpful messages  
- **`tests/unit/test_sequencer.py`** - Sequencer behavior: Insert/renumber maps; collisions; batch updates
- **`tests/unit/test_streaming_parser.py`** - Streaming parser guardrails: Large files, chunking, recovery/resume
- **`tests/unit/test_registries.py`** - Registry validation: Shape, invariants, duplicate checking

### Plugin Tests
- **`tests/plugins/test_plugin_registry.py`** - Plugin discovery/execution: Manifest loading, capability map, import failures
- **`tests/plugins/test_plugin_permissions.py`** - Security regression tests: Enforce IO/Network policies; deny violations; logging

### Integration Tests
- **`tests/integration/test_import_export.py`** - End-to-end import/export: Prose→YAML→MD roundtrips; stability; determinism
- **`tests/integration/test_plugins.py`** - Plugin system: Manifest loading, sandbox enforcement, capability resolution
- **`tests/integration/test_cli_watch.py`** - End-to-end watch loop: Change detection → engine → artifacts; idempotency; recovery

### Test Fixtures
- **`tests/fixtures/`** - Test data: Sample YAML files, prose docs, expected outputs

## System Rules & Invariants (must-follow)

### 1) IDs & StepKey
1. **Format:** `MAJOR.FRAC` where `MAJOR` is `1..n`, `FRAC` is a decimal with **≥3** digits; additional digits permitted for midpoints
2. **Ordering:** Lexicographic; supports `insert_after()`/`insert_before()` via midpoint generation
3. **Uniqueness:** Within ProcessFlow scope; collision detection required
4. **Precision:** Governed by `registries/naming.yaml` (default 3 digits)

### 2) Source of Truth
5. **YAML First:** Process spec YAML is the **only** source of truth for content. MD/Draw.io are derived artifacts
6. **Determinism:** Exporters MUST be idempotent: same YAML → byte-identical artifacts (timestamps and volatile data excluded)

### 3) Naming & Registries
7. **Actors/Actions:** Must appear in `registries/*.yaml`. Unknown values cause **ERROR** diagnostics
8. **Plugin IDs:** Lowercase dot-separated: `<org>.<package>.<n>` (e.g., `apf.diagram_generator`). No spaces, only `[a-z0-9_.-]`
9. **File Layout:** Artifacts land under `dist/<run_id>/...` (CI) or `derived/` (local), as configured

### 4) Validation
10. **Schema then Semantics:** Validators run JSON Schema checks first, then semantic invariants (connectivity, uniqueness, guard completeness)
11. **Severity Levels:** `ERROR` (blocks export), `WARN` (export allowed), `INFO` (advisory). Codes follow `APF####` pattern
12. **Branching:** Every `Branch` must have exhaustive guards or a default path; merges require explicit nodes

### 5) Import/Export
13. **Importer Rules:** `prose_to_yaml` must normalize using registries; ambiguous sentences yield **WARN** with suggested resolutions
14. **Exporter Rules:** `drawio` exporter must emit stable geometry keyed by StepKey; MD exporter emits **one line per step** and branch cues

### 6) Plugins & Manifests
15. **Least-Privilege:** Manifests declare IO globs and network = **deny by default**. CI fails if manifest is over-permissive
16. **Capability Names:** Kebab or dot notation; MUST match implemented entry points
17. **Compat Ranges:** Plugins declare `apf_core` compatibility using semver ranges; executor refuses mismatches

### 7) Security & Recovery
18. **Sandbox:** Plugins run in temp workspaces; only declared globs are readable/writable
19. **Snapshots:** Inputs and produced artifacts are snapshotted; audit log records content hashes
20. **Transactions:** Renumber and write-backs occur within a transaction; on failure, **no partial effects** persist

### 8) Orchestration
21. **Job Model:** Each job is pure relative to input set; retriable with exponential backoff; idempotent when replayed
22. **Fan-out/Fan-in:** Coordinator may parallelize exports; artifacts must not race (unique paths per target)

### 9) Library & Templates
23. **Template IDs:** `lib.<domain>.<n>@<semver>`; resolving without version pins latest **compatible**
24. **Migrations:** Library schema changes ship up/down migrations and seed verification

### 10) Parser & Streaming
25. **Chunking:** Streaming parser reads in bounded chunks; yields progressive diagnostics tagged by byte/line offsets
26. **Resumability:** Checkpoints recorded in state store; watch loop resumes from last good offset

### 11) Watch Loop & Artifacts
27. **Debounce:** File change debounce **≥ 500 ms**; coalesce bursts
28. **Artifact Naming:** Stable filenames with content hashes for cache invalidation

## Test Patterns & Examples

### Registry Tests Pattern
```python
def test_actors_registry_shape():
    """Validate actors.yaml has required structure and no duplicates."""
    actors_path = Path("registries/actors.yaml")
    assert actors_path.exists(), "actors.yaml missing"
    
    with open(actors_path) as f:
        data = yaml.safe_load(f)
    
    # Check for duplicates
    ids = [actor["id"] for actor in data["actors"]]
    assert len(ids) == len(set(ids)), "Duplicate actor IDs found"
```

### Schema Validation Pattern
```python
@pytest.fixture
def diagnostics_schema():
    schema_path = Path("schemas/diagnostics.schema.json")
    with open(schema_path) as f:
        return json.load(f)

def test_valid_diagnostic_example(diagnostics_schema):
    valid_diagnostics = [{"severity": "ERROR", "code": "APF0001", "message": "Test"}]
    validate(instance=valid_diagnostics, schema=diagnostics_schema)
```

## CI Integration Requirements

### Essential CI Jobs
1. **Registry Validation** - Ensure controlled vocabularies remain consistent
2. **Schema Tests** - Validate JSON schemas and example compliance
3. **Unit Test Coverage** - Core logic validation
4. **Integration Tests** - End-to-end workflow validation
5. **Plugin Manifest Validation** - Security and capability checks

### Test Dependencies
```toml
[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pyyaml>=6.0", 
  "jsonschema>=4.22",
]
```

## Key Terms & Glossary

- **Capability:** A named operation exposed by a plugin (e.g., `import.prose`, `seq.insert`, `export.drawio`)
- **Manifest:** A `plugin.yaml` that declares id, version, capabilities, permissions, and compatibility ranges
- **Executor:** The safe runtime wrapper that runs a plugin with policy enforcement and recovery hooks
- **Job:** A unit of work (e.g., *parse file X*, *export MD*). Jobs are queued, retried, and audited
- **Run:** A correlated execution session identified by `run_id` across logs, artifacts, and audit entries
- **Snapshot:** Content-addressed capture of inputs/outputs for recovery and provenance
- **Transaction:** A scoped context that guarantees **all-or-nothing** application of effects
- **Audit Log:** Append-only event stream for compliance and debugging
- **Policy:** Security rules governing filesystem/network access and data classes permitted to plugins
- **Sandbox:** The constrained environment provided to plugins (temp dirs, read-only mounts, resource limits)
- **State Store:** A versioned repository of document/editor state with autosave and restore
- **Template (Library):** A reusable step or fragment identified by `template_id@version`
- **Streaming Parser:** An incremental parser that processes large documents in bounded memory
- **Watch Loop:** A daemon that detects file changes, enqueues jobs, and refreshes artifacts deterministically
- **Artifact:** A deterministic output (YAML/JSON/MD/Draw.io) with stable filenames and hashes