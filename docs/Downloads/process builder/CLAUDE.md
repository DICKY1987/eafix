# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Validation and Linting
- `python apf_apply_stub.py --validate-only spec/master.yaml` - Validate master YAML file
- `python apf_apply_stub.py --lint-cr changes/*.yaml` - Lint change request YAML files
- Pre-commit hooks run these validations automatically

### Testing
- Run individual test files: `python -m pytest tests/schemas/test_diagnostics_schema.py`
- Run all tests in a directory: `python -m pytest tests/`
- Test files are located in `tests/` and `process_tool/tests/`

### APF Operations
- Apply change request (dry run): `python apf_apply_stub.py --apply path/to/cr.yaml --dry-run`
- Apply change request: `python apf_apply_stub.py --apply path/to/cr.yaml`

## Architecture Overview

This is the **Atomic Process Framework (APF)** - a system for managing structured process documentation with atomic operations, validation, and multi-format export capabilities.

### Core Architecture

**Two-Layer Structure:**
1. **BU_TOOL/** - Business layer with application stubs and high-level components
2. **process_tool/** - Technical implementation with full module structure

**Key Architectural Patterns:**
- **Atomic Operations**: All process changes are applied as atomic transactions with rollback capability
- **Registry-Based**: Actions and actors are defined in YAML registries (`registries/actions.yaml`, `registries/actors.yaml`)
- **Plugin Architecture**: Extensible through plugins in `plugins/` directory
- **Multi-Application**: Supports CLI, desktop GUI, and service applications

### Core Components

**Process Models** (`process_tool/core/models.py`):
- `ProcessFlow` - Complete process documentation container
- `ProcessStep` - Individual atomic actions with SLA and validation
- `ProcessSection` - Major process groupings
- `SubProcess` - Reusable process components

**Validation System** (`schemas/diagnostics.schema.json`):
- Structured diagnostics with severity levels (ERROR, WARN, INFO)
- Step-level validation using step IDs (pattern: `\d+(\.\d{3,})?`)
- JSON Schema validation with diagnostic codes (APFxxxx format)

**Change Request System** (`apf_apply_stub.py`):
- YAML-based change requests with precondition checking
- SHA256 validation for target files
- Atomic apply/rollback operations with audit logging

### Module Organization

**Applications Layer** (`process_tool/applications/`):
- `cli/` - Command-line interface
- `desktop/` - GUI application with editors and widgets
- `service/` - REST API service layer

**Core Framework** (`process_tool/core/`):
- Foundation and contracts for system bootstrap
- Data models and validation rules
- Central validation engine

**Import/Export Engine** (`process_tool/import_export/`):
- Multi-format support (JSON, YAML, Markdown, Draw.io)
- Prose import with NLP capabilities
- Structured export with templating

**Plugin System** (`process_tool/plugins/`):
- Base plugin architecture with registry
- Analysis plugins for metrics and validation
- Loadable plugin discovery

**Security Layer** (`process_tool/security/`):
- Authentication and permission system
- Runtime security with sandboxing
- Policy enforcement framework

**Recovery System** (`process_tool/recovery/`):
- Transaction management with snapshots
- Audit logging and state persistence
- Rollback capabilities with state backends

### Registry System

**Actions Registry** (`registries/actions.yaml`):
Defines 8 categories of atomic operations:
- IO (import, export, render)
- TRANSFORM (parse, normalize, transform, sequence)
- DECISION (decide)
- QUALITY (validate)
- CONTROL (wait)
- COMM (notify)
- STATE (snapshot, transact, archive)
- SECURITY (policy enforcement)

Each action includes synonyms, descriptions, and diagram styling.

**Step ID Format**: `\d+(\.\d{3,})?` (e.g., "1.001", "12.0015")
- Major version + 3+ digit minor for atomic step identification
- Used throughout validation and change tracking

### Testing Strategy

Tests are organized by module with schema validation tests for:
- Diagnostics schema compliance
- Registry validation
- Step ID pattern validation
- JSON roundtrip serialization

The codebase uses PyYAML for YAML processing and jsonschema for validation.