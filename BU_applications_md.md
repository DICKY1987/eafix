# Applications

> User-facing applications: CLI tools, web service, and desktop interface.

## Application Architecture Overview

The APF provides three primary application interfaces:
1. **CLI Tools** - Command-line interface for automation and CI/CD
2. **HTTP Service** - FastAPI-based web service for integration
3. **Desktop App** - PySide6-based GUI for interactive editing

All applications are thin wrappers around the core engine, ensuring consistent behavior across interfaces.

## 1. CLI Application (`apps/cli/`)

### Structure
```
apps/cli/apf/
├── __init__.py          # CLI package marker, console entry point
├── __main__.py          # CLI entry point with argparse/Typer wiring
└── commands/
    ├── export.py        # apf export subcommand
    ├── validate.py      # apf validate subcommand  
    ├── seq.py          # apf seq subcommand
    └── watch.py        # apf watch daemon
```

### CLI Entry Point (`apps/cli/apf/__init__.py`)
**Purpose:** CLI package marker and console entry point exposure
**Key responsibilities:**
- Expose console entry point for installation
- Import and configure logging
- Handle version display

### Main CLI Handler (`apps/cli/apf/__main__.py`) 
**Purpose:** CLI entry point with argument parsing
**Key responsibilities:**
- Argparse/Typer wiring for subcommands
- Global flags (--verbose, --config, --help)
- Subcommand dispatch to plugin system
- Exception handling and exit codes
- Configuration loading and validation

### Export Command (`apps/cli/apf/commands/export.py`)
**Purpose:** `apf export` subcommand implementation
**Key responsibilities:**
- Load file → exporter(s) → write artifacts workflow
- Support multiple export formats (MD, Draw.io, JSON, etc.)
- Handle output directory management
- Provide progress feedback and error reporting
- Return appropriate exit codes (0=success, 1=error, 2=warnings)

**Command signature:**
```bash
apf export <input.yaml> [--format=md,drawio] [--output-dir=dist/] [--verbose]
```

### Validate Command (`apps/cli/apf/commands/validate.py`)
**Purpose:** `apf validate` subcommand implementation
**Key responsibilities:**
- Run schema + semantic validation checks
- Print diagnostics in table format or NDJSON
- Support filtering by severity level
- Generate machine-readable output for CI integration
- Exit with error code if validation fails

**Command signature:**
```bash
apf validate <input.yaml> [--format=table|json] [--severity=error,warn,info]
```

### Sequencing Command (`apps/cli/apf/commands/seq.py`)
**Purpose:** `apf seq` subcommand for step numbering operations
**Key responsibilities:**
- Insert/renumber operations with dry-run support
- Create backup files before modification
- Handle StepKey collision resolution
- Support batch operations across multiple files
- Maintain step ordering invariants

**Command signature:**
```bash
apf seq insert <input.yaml> --after=1.001 [--dry-run] [--backup]
apf seq renumber <input.yaml> [--start=1.001] [--increment=0.001]
```

### Watch Daemon (`apps/cli/apf/commands/watch.py`)
**Purpose:** Watch daemon for zero-touch continuous processing
**Key responsibilities:**
- File watcher → enqueue jobs → engine run → artifact refresh
- Debouncing and throttling of file change events (≥500ms)
- Background job execution with progress tracking
- Error recovery and retry logic
- Clean shutdown and resource management

**Dependencies:** Orchestrator, parser, exporters, state management
**Command signature:**
```bash
apf watch <directory> [--patterns="*.yaml"] [--debounce=500ms]
```

## 2. HTTP Service (`apps/service/`)

### Structure
```
apps/service/
├── main.py       # FastAPI app factory
├── routes.py     # HTTP endpoints
└── watch.py      # Service-side file watcher (optional)
```

### FastAPI Application (`apps/service/main.py`)
**Purpose:** FastAPI application factory and configuration
**Key responsibilities:**
- Dependency injection container setup
- Application lifespan management (startup/shutdown)
- Logging configuration and middleware
- CORS and security headers
- Health check endpoints
- OpenAPI documentation generation

**Dependencies:** Core engine components, configuration system

### HTTP Routes (`apps/service/routes.py`)
**Purpose:** REST API endpoints for APF operations
**Key responsibilities:**
- `/validate` - Validation endpoint with streaming diagnostics
- `/export` - Export endpoint returning generated artifacts
- `/decide` - Decision support for process optimization
- Stream diagnostics in real-time during processing
- Handle file uploads and multipart requests
- Return structured error responses

**API Endpoints:**
```
POST /validate        # Validate process definition
POST /export         # Export to various formats  
POST /decide         # Get optimization recommendations
GET  /health         # Health check
GET  /docs          # OpenAPI documentation
```

### Service-side Watcher (`apps/service/watch.py`)
**Purpose:** Optional background file monitoring service
**Key responsibilities:**
- Background task to monitor repositories or job queues
- Hot-reload artifacts when source files change
- WebSocket notifications for real-time updates
- Integration with external CI/CD systems
- Queue management and job scheduling

## 3. Desktop Application (`apps/desktop/`)

### Structure
```
apps/desktop/
├── main.py                    # PySide6 launcher
├── ui_shell.py               # Main window shell
└── editors/
    └── yaml_editor.py        # Schema-aware YAML editor
```

### Desktop Launcher (`apps/desktop/main.py`)
**Purpose:** PySide6 application bootstrap
**Key responsibilities:**
- Application bootstrap and initialization
- Menu system configuration (File, Edit, View, Tools, Help)
- Theme management and system integration
- Telemetry opt-in dialog and privacy controls
- Exception handling and crash reporting
- Auto-updater integration

**Framework choice:** PySide6 for native desktop experience

### Main Window Shell (`apps/desktop/ui_shell.py`)
**Purpose:** Main window container and layout management
**Key responsibilities:**
- Dockable layout with panels (Inspector, Problems, Console)
- Status bar with progress indicators and notifications
- Error panel integration with diagnostics system
- Command palette (Ctrl+Shift+P) for quick actions
- Activity center for long-running tasks
- Project/file management sidebar

**Key UI Components:**
- Central workspace (tabbed document area)
- Dockable panels (Inspector, Problems, Console, Explorer)
- Toolbar with common actions
- Status bar with validation feedback

### YAML Editor (`apps/desktop/editors/yaml_editor.py`)
**Purpose:** Schema-aware YAML editing with live validation
**Key responsibilities:**
- Live validation with real-time diagnostic feedback
- StepKey helper functions (insert, renumber, navigate)
- Jump-to-diagnostic functionality from Problems panel
- Diff view for comparing versions
- Syntax highlighting and auto-completion
- Schema-aware IntelliSense for APF constructs

**Features:**
- Syntax highlighting for YAML + APF extensions
- Real-time validation with error/warning indicators
- Auto-completion for actors, actions, and StepKeys
- Folding for complex process sections
- Search and replace with StepKey awareness

## Cross-Application Features

### Configuration System
All applications share a unified configuration system:
- **Default config:** `config/default_config.yaml`
- **User overrides:** `~/.config/apf/config.yaml` 
- **Environment variables:** `APF_*` prefix
- **Command-line flags:** Override any config value

### Error Handling & Diagnostics
Consistent error handling across all applications:
- Structured diagnostics with severity levels
- Correlation IDs for cross-application debugging
- Graceful degradation on plugin failures
- User-friendly error messages with remediation hints

### Plugin Integration
All applications integrate with the plugin system:
- Dynamic capability discovery
- Sandboxed plugin execution
- Permission-based access control
- Plugin failure isolation

### Logging & Observability
Unified logging and telemetry:
- Structured logging with correlation IDs
- Performance metrics collection
- Usage analytics (with user consent)
- Crash reporting and diagnostics

## GUI Design System & Accessibility

### Framework Selection (PySide6/Qt6)
**Rationale:** 
- Mature widget ecosystem with docking support
- Native desktop integration and performance
- Strong accessibility APIs (WCAG 2.2 compliance)
- Professional appearance and behavior
- Cross-platform consistency

### Design Principles
- **WCAG 2.2 Compliance:** Target size ≥24×24px, visible focus rings, keyboard parity
- **Docking Layout:** Flexible workspace with user-configurable panels
- **Progressive Disclosure:** Complex features behind advanced modes
- **Contextual Help:** F1 help, tooltips, and guided tours
- **Keyboard-First:** Full keyboard navigation and shortcuts

### Accessibility Features
- Screen reader support via Qt accessibility APIs
- High contrast theme support
- Keyboard alternatives for all drag operations
- Focus management and tab order
- Color-blind friendly color schemes

## Development & Testing

### Dependencies
```toml
[project.dependencies]
# CLI
typer = ">=0.9.0"          # CLI framework
rich = ">=13.0.0"          # Terminal formatting

# Service  
fastapi = ">=0.104.0"      # Web framework
uvicorn = ">=0.24.0"       # ASGI server

# Desktop
PySide6 = ">=6.6.0"        # GUI framework
```

### Testing Strategy
- **Unit tests:** Individual command/component testing
- **Integration tests:** End-to-end workflow testing
- **UI tests:** Automated GUI testing (desktop)
- **API tests:** HTTP endpoint validation (service)

### Packaging & Distribution
- **CLI:** Console scripts entry point
- **Service:** Docker container + systemd service
- **Desktop:** Platform-specific installers (MSI, DMG, AppImage)

This architecture ensures consistent functionality across all user interfaces while providing appropriate interaction patterns for each use case.