# APF (Atomic Process Framework) File Tree

```
apf-system/
├── pyproject.toml                              # Top-level Python/monorepo configuration
├── .pre-commit-config.yaml                     # Pre-commit hooks configuration
├── .github/
│   └── workflows/
│       └── ci.yml                              # CI pipeline configuration
├── config/
│   └── defaults.yaml                           # Default system configuration
├── schemas/                                    # JSON Schema definitions
│   ├── atomic_process.schema.json              # Core ProcessFlow/AtomicStep/Branch schema
│   ├── plugin.manifest.schema.json             # Plugin manifest validation schema
│   ├── library.schema.json                     # Reusable step/recipe library schema
│   └── diagnostics.schema.json                 # Structured diagnostics schema
├── registries/                                 # Controlled vocabularies
│   ├── actors.yaml                             # Actor names/IDs registry
│   ├── actions.yaml                            # Action verbs registry
│   ├── naming.yaml                             # Naming conventions (StepKey precision, etc.)
│   └── prose_rules.yaml                        # Text→action mapping rules
├── example_files/                              # Reference examples and demos
│   ├── demo_atomic.yaml                        # Realistic demo process spec
│   └── hello_world.yaml                        # Minimal "hello world" spec
├── packages/                                   # Core system packages
│   ├── apf_common/                             # Foundation utilities
│   │   └── src/apf_common/
│   │       ├── __init__.py                     # Common surface exports
│   │       ├── config.py                       # Typed config loader/merger
│   │       ├── paths.py                        # Centralized path resolution
│   │       ├── logging.py                      # Structured logging utilities
│   │       └── errors.py                       # Common exception types
│   ├── apf_core/                               # Core models and validation
│   │   └── src/apf_core/
│   │       ├── __init__.py                     # Public API surface
│   │       ├── models/
│   │       │   ├── __init__.py                 # Model exports
│   │       │   ├── ids.py                      # StepKey/Process ID primitives
│   │       │   ├── step.py                     # AtomicStep Pydantic model
│   │       │   ├── branch.py                   # Decision/branch constructs
│   │       │   └── process_flow.py             # ProcessFlow aggregate model
│   │       └── validation/
│   │           ├── __init__.py                 # Validation entrypoint
│   │           ├── schema_loader.py            # JSON Schema resolver/compiler
│   │           ├── diagnostics.py              # Rich diagnostic types
│   │           └── validator.py                # Schema + semantic validation
│   ├── import_export/                          # Format conversion engine
│   │   └── src/import_export/
│   │       ├── __init__.py                     # Import/export surface
│   │       ├── importers/
│   │       │   ├── __init__.py                 # Importer registry
│   │       │   ├── prose_importer.py           # Structured prose → YAML
│   │       │   └── yaml_importer.py            # YAML loader/normalizer
│   │       └── exporters/
│   │           ├── __init__.py                 # Exporter registry
│   │           ├── markdown_exporter.py        # ProcessFlow → Markdown
│   │           ├── drawio_exporter.py          # ProcessFlow → draw.io XML
│   │           └── json_exporter.py            # ProcessFlow → JSON
│   ├── sequencing/                             # StepKey management
│   │   └── src/sequencing/
│   │       ├── __init__.py                     # Sequencing surface
│   │       ├── step_key.py                     # StepKey manipulation logic
│   │       └── sequencer.py                    # High-level sequencer operations
│   ├── editing/                                # Programmatic editing
│   │   └── src/editing/
│   │       ├── __init__.py                     # Editing surface
│   │       ├── editor.py                       # Programmatic YAML editor
│   │       └── edit_script.py                  # Edit script parser/executor
│   ├── huey_core/                              # Plugin runtime system
│   │   └── src/huey_core/
│   │       ├── __init__.py                     # Plugin runtime surface
│   │       ├── manifest.py                     # Plugin manifest loader/validator
│   │       ├── executor.py                     # Safe plugin execution wrapper
│   │       └── policy.py                       # Security policy enforcement
│   ├── recovery/                               # State management and recovery
│   │   └── src/recovery/
│   │       ├── __init__.py                     # Recovery entrypoint
│   │       ├── snapshot.py                     # Content-addressed snapshots
│   │       ├── transaction.py                  # Transaction/rollback context
│   │       └── audit_log.py                    # Append-only audit trail
│   ├── state/                                  # Document state and versioning
│   │   └── src/state/
│   │       ├── __init__.py                     # State/versioning entrypoint
│   │       └── documentation_state.py          # Document state manager
│   ├── orchestration/                          # Job coordination
│   │   └── src/orchestration/
│   │       ├── __init__.py                     # Orchestration surface
│   │       ├── state.py                        # Runtime state machines
│   │       ├── jobs.py                         # Job definitions & queues
│   │       └── coordinator.py                  # High-level execution coordinator
│   ├── process_library/                        # Reusable templates
│   │   └── src/process_library/
│   │       ├── __init__.py                     # Library surface
│   │       ├── db.py                           # SQLite access layer
│   │       ├── migrations.py                   # Database migrations
│   │       └── templates.py                    # Step template resolution
│   └── apf_parser/                             # Document parsing
│       └── src/apf_parser/
│           ├── __init__.py                     # Parser entrypoint
│           ├── structured_document.py          # Deterministic doc parser
│           └── streaming.py                    # Incremental parser for large docs
├── plugins/                                    # First-party plugins
│   ├── atomic_process_engine/
│   │   ├── plugin.yaml                         # Engine plugin manifest
│   │   └── plugin.py                           # Import→validate→export orchestrator
│   ├── step_sequencer/
│   │   ├── plugin.yaml                         # Sequencing plugin manifest
│   │   └── plugin.py                           # Insert/renumber plugin commands
│   ├── process_standardizer/
│   │   ├── plugin.yaml                         # Standardizer plugin manifest
│   │   └── plugin.py                           # Prose normalization plugin
│   ├── diagram_generator/
│   │   ├── plugin.yaml                         # Diagram generator manifest
│   │   └── plugin.py                           # Draw.io/Mermaid export wrapper
│   ├── validation_engine/
│   │   ├── plugin.yaml                         # Deep validation manifest
│   │   └── plugin.py                           # Advanced invariant enforcement
│   └── documentation/
│       ├── plugin.yaml                         # Doc bundler manifest
│       └── plugin.py                           # Documentation bundle generator
├── apps/                                       # User-facing applications
│   ├── cli/                                    # Command-line interface
│   │   └── apf/
│   │       ├── __init__.py                     # CLI package marker
│   │       ├── __main__.py                     # CLI entry point
│   │       └── commands/
│   │           ├── export.py                   # apf export subcommand
│   │           ├── validate.py                 # apf validate subcommand
│   │           ├── seq.py                      # apf seq subcommand
│   │           └── watch.py                    # Watch daemon for auto-refresh
│   ├── service/                                # Web service (FastAPI)
│   │   ├── main.py                             # FastAPI app factory
│   │   ├── routes.py                           # HTTP endpoints
│   │   └── watch.py                            # Service-side file watcher
│   └── desktop/                                # Desktop GUI (PySide6)
│       ├── main.py                             # PySide6 launcher
│       ├── ui_shell.py                         # Main window shell
│       └── editors/
│           └── yaml_editor.py                  # Schema-aware YAML editor
├── tests/                                      # Test infrastructure
│   ├── unit/                                   # Unit tests
│   │   ├── test_step_key.py                    # StepKey correctness tests
│   │   ├── test_validation.py                  # Validator behavior tests
│   │   ├── test_registries.py                  # Registry validation tests
│   │   └── test_diagnostics_schema.py          # Diagnostics schema tests
│   ├── integration/                            # Integration tests
│   │   ├── test_import_export.py               # End-to-end import/export tests
│   │   └── test_plugins.py                     # Plugin system tests
│   └── fixtures/                               # Test data
│       ├── sample_yaml_files/                  # Sample YAML specs
│       ├── prose_documents/                    # Sample prose docs
│       └── expected_outputs/                   # Expected test outputs
├── docs/                                       # Documentation
│   ├── api/                                    # API documentation
│   ├── tutorials/                              # User tutorials
│   ├── architecture/                           # Architecture decisions
│   └── migrations/                             # Schema migration guides
├── derived/                                    # Generated artifacts (local)
│   ├── markdown/                               # Generated Markdown files
│   ├── diagrams/                               # Generated diagrams
│   └── json/                                   # Generated JSON exports
└── dist/                                       # CI/Build artifacts
    └── <run_id>/                               # Run-specific artifact directories
        ├── markdown/
        ├── diagrams/
        └── json/
```

## Key Components Overview

### **Bootstrap & Contracts** (Foundation)
- Configuration files, schemas, and registries that define system contracts
- JSON schemas for validation and structure enforcement
- Controlled vocabularies for actors, actions, and naming conventions

### **Core Packages** (Business Logic)
- **apf_common**: Foundational utilities (logging, config, paths, errors)
- **apf_core**: Core models and validation (StepKey, ProcessFlow, diagnostics)
- **import_export**: Format conversion between YAML, Markdown, draw.io, JSON
- **sequencing/editing**: StepKey management and programmatic editing
- **huey_core**: Plugin system with secure execution and policy enforcement

### **Advanced Packages** (System Services)
- **recovery/state**: Snapshots, transactions, audit trails, document versioning
- **orchestration**: Job coordination and execution planning
- **process_library**: Reusable step templates and database management
- **apf_parser**: Document parsing with streaming capabilities

### **Plugins** (Feature Extensions)
- Modular capabilities for processing, validation, and export
- Each plugin has manifest (plugin.yaml) + implementation (plugin.py)
- Safe execution with sandboxing and policy enforcement

### **Applications** (User Interfaces)
- **CLI**: Command-line tools with subcommands and watch daemon
- **Service**: FastAPI web service with REST endpoints
- **Desktop**: PySide6 GUI with schema-aware editor

### **Quality Assurance**
- Comprehensive test coverage (unit, integration, fixtures)
- CI/CD pipeline with quality gates
- Pre-commit hooks for code quality
