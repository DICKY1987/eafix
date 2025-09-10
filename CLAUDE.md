# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a comprehensive trading system with **dual architecture** combining:
1. **Legacy monolithic trading system** (root directory) with Excel-like GUI and MetaTrader 4 integration
2. **Modern microservices architecture** (`eafix-modular/`) with containerized services and event-driven design

**Legacy Architecture**: Hybrid system with traditional trading components and APF integration
**Modern Architecture**: Event-driven microservices with FastAPI, Redis pub/sub, and Docker containers
**Focus**: Production trading system with comprehensive protection, analysis, and monitoring capabilities
**Languages**: Python 3.11+ (microservices), Python 3.x (legacy), MQL4 (MetaTrader integration)
**Databases**: 
  - Legacy: SQLite (trading_system.db, huey_project_organizer.db)
  - Modern: PostgreSQL with Redis message bus

## Key Development Commands

### Modern Microservices Commands (eafix-modular/)

```bash
# Navigate to microservices directory
cd eafix-modular/

# Project setup
poetry install                          # Install all dependencies
poetry run pre-commit install           # Install git hooks
make install                             # Combined setup command

# Docker operations
make docker-up                          # Start entire system with Docker Compose
make docker-down                        # Stop all services
make docker-logs                        # Follow container logs
docker compose -f deploy/compose/docker-compose.yml up -d --build

# Development - individual service
cd services/data-ingestor
poetry run python -m src.main          # Run service directly
REDIS_URL=redis://localhost:6379 poetry run python -m src.main  # With env vars

# Testing
make test-all                           # Run full test suite
poetry run pytest                       # Run all tests with Poetry
poetry run pytest services/data-ingestor/tests/  # Test specific service
poetry run pytest --cov=services       # Run with coverage
make smoke                              # End-to-end health verification

# Contract validation
make contracts-validate-full            # Comprehensive schema validation
make contracts-validate                 # JSON schemas only
make csv-validate                       # CSV format validation
make reentry-validate                   # Shared library validation
make contracts-compat                   # Schema backward compatibility

# Code quality
make format                             # Format code with black and isort
make lint                               # Run linting and type checks
poetry run black services/              # Format code
poetry run flake8 services/             # Lint code
poetry run mypy services/*/src          # Type checking

# Performance testing
make replay-test                        # Tick replay performance test
python scripts/replay/replay_ticks.py data.csv --url http://localhost:8081/ingest/manual

# Production readiness
make gaps-check                         # Review production gaps and SLOs
```

### Legacy System Commands

#### Main Application Launch
```bash
# Primary system launcher (unified Excel-like interface)
python launch_trading_system.py

# APF desktop application
python -m eafix.apps.desktop.main

# Alternative launcher scripts
launch_gui.bat    # Windows
launch_gui.sh     # Unix/Linux
```

### EAFIX CLI Tool System
```bash
# Main CLI entry point (unified command interface)
python eafix_cli.py --help                      # Show all available commands
python eafix_cli.py version                     # Show version information
python eafix_cli.py status                      # Quick system status check

# Trading operations
python eafix_cli.py trade signals               # View trading signals
python eafix_cli.py trade positions             # View current positions
python eafix_cli.py trade start                 # Start automated trading
python eafix_cli.py trade stop                  # Stop automated trading
python eafix_cli.py trade calendar              # Economic calendar

# Guardian protection system
python eafix_cli.py guardian status             # Guardian system status
python eafix_cli.py guardian constraints        # Manage constraints
python eafix_cli.py guardian gates              # Check gate system
python eafix_cli.py guardian alerts             # Recent alerts
python eafix_cli.py guardian emergency          # Emergency controls

# System management
python eafix_cli.py system health               # Comprehensive health check
python eafix_cli.py system monitor              # Real-time monitoring
python eafix_cli.py system config               # Configuration management
python eafix_cli.py system logs                 # View system logs
python eafix_cli.py system backup               # Create backup

# Market analysis
python eafix_cli.py analyze currency-strength   # Currency strength analysis
python eafix_cli.py analyze positioning         # Institutional positioning
python eafix_cli.py analyze indicators EURUSD   # Technical indicators
python eafix_cli.py analyze report daily        # Generate reports
python eafix_cli.py analyze scan                # Market opportunity scanner

# Setup and configuration
python eafix_cli.py setup install               # Install dependencies
python eafix_cli.py setup init                  # Initialize project
python eafix_cli.py setup test-install          # Test installation
python eafix_cli.py setup configure             # Configure system
python eafix_cli.py setup doctor                # System diagnostics

# Deployment (Windows/Unix)
deploy_cli.bat                                   # Windows deployment
./deploy_cli.sh                                  # Unix/Linux deployment
```

### CLI Development Framework (Legacy)
```bash
# Cross-platform development setup (in CLI_FILES/)
bash CLI_FILES/cross_platform_setup.sh          # Initialize development environment
bash CLI_FILES/practical_implementation.sh       # Apply practical configurations

# Multi-CLI orchestration (see CLI_FILES/multi_cli_orchestrator.txt for configuration)
# Zero-touch automation setup (see CLI_FILES/zero_touch_setup.txt for details)
```

### Testing Framework
```bash
# Main test suite (pytest configured with src/ pythonpath)
pytest -q                                      # Quick test run with minimal output
pytest -v                                      # Verbose test output
pytest tests/                                  # Run all tests

# Run specific test files
pytest tests/test_friday_vol_signal.py         # Friday volatility signal tests
pytest tests/test_currency_strength.py         # Currency strength analysis tests
pytest tests/test_conditional_signals.py       # Conditional signal tests
pytest tests/test_economic_calendar.py         # Economic calendar tests
pytest tests/test_core_startup.py              # Core system startup tests
pytest tests/test_database_operations.py       # Database layer tests
pytest tests/test_dde_connection.py            # DDE communication tests
pytest tests/test_indicators.py                # Technical indicator tests
pytest tests/test_system_integration.py        # End-to-end integration tests

# Run tests for specific components
pytest tests/ -k "friday"                      # Run tests containing 'friday'
pytest tests/ -k "database"                    # Run tests containing 'database'
pytest tests/ -k "signal"                      # Run tests containing 'signal'

# Test with coverage (if installed)
pytest --cov=src tests/                        # Coverage report
```

### Trading Tools and Analysis
```bash
# Comprehensive trading framework analysis (run from root directory)
python tools/trading_framework_scan.py      # Scan system for issues
python tools/detect_trading_issues.py       # Detect configuration problems
python tools/run_trading_validation.py      # Validate trading setup
python tools/compute_trading_metrics.py     # Calculate system metrics
python tools/apply_trading_patch.py         # Apply fixes and patches
python tools/map_trading_remediations.py    # Map remediation strategies
python tools/make_trading_diff.py           # Generate trading system diffs

# Results are saved to *_results.json files in root directory
```

### Parallel Integration Commands
```bash
# Parallel development stream integration (99% system completion)
python run_parallel_integration.py    # Run full parallel integration
python -m eafix.integration.stream_integrator # Direct integration runner

# Individual stream validation
python -c "from src.eafix.integration.stream_integrator import StreamIntegrator; si = StreamIntegrator('.'); print(si.integrate_stream_a_testing())"
python -c "from src.eafix.integration.stream_integrator import StreamIntegrator; si = StreamIntegrator('.'); print(si.integrate_stream_b_indicators())"
```

### APF Commands (Legacy)
```bash
# APF CLI operations
python -m eafix.apps.cli.apf export   # Export process definitions
python -m eafix.apps.cli.apf validate # Validate process schemas
python -m eafix.apps.cli.apf seq      # Sequence management
```

## Architecture Overview

### Dual Architecture System

**Modern Microservices Architecture** (`eafix-modular/`)
- **Event-Driven Design**: FastAPI services with Redis pub/sub messaging
- **12 Core Services**: Complete trading pipeline from data ingestion to execution
- **Container-First**: Docker Compose for development, Kubernetes-ready
- **Contract Registry**: Centralized schema validation and data integrity
- **Shared Libraries**: Cross-service components with Python/MQL4 parity

**Legacy Trading System** (Root level)
- **Core Components** (`core/`): AppController, DatabaseManager, EAConnector, ConstraintRepository
- **Tab System** (`tabs/`): Modular GUI tabs for trading functions
- **MT4 Integration** (`mt4_dde_interface/`): Direct MetaTrader 4 communication
- **Main Launcher** (`launch_trading_system.py`): Unified Excel-like interface entry point

**APF Integration** (`src/eafix/`)
- **Modern Package Structure**: Standard Python package with proper imports
- **Guardian System** (`src/eafix/guardian/`): Multi-agent constraint protection
- **Process Framework** (`src/eafix/apps/`): CLI, desktop, and service applications
- **Signal Processing** (`src/eafix/signals/`): Advanced trading signals
- **Indicators** (`src/eafix/indicators/`): Technical analysis components

### Modern Microservices Components (eafix-modular/)

**Core Trading Pipeline**:
1. **data-ingestor** (8081): Normalizes MT4/DDE price feeds → `PriceTick@1.0` events
2. **indicator-engine** (8082): Computes technical indicators → `IndicatorVector@1.1` events  
3. **signal-generator** (8083): Applies trading rules → `Signal@1.0` events
4. **risk-manager** (8084): Position sizing/risk validation → `OrderIntent@1.2` (HTTP API)
5. **execution-engine** (8085): Broker order execution → `ExecutionReport@1.0` events

**Supporting Services**:
- **calendar-ingestor** (8086): Economic calendar processing → `CalendarEvent@1.0` events
- **reentry-matrix-svc** (8087): Re-entry decision logic → `ReentryDecision@1.0` events
- **reporter** (8088): Metrics and P&L analysis
- **gui-gateway** (8080): API gateway for operator UI

**Runtime Flow Integration Services**:
- **flow-orchestrator**: Event-driven flow coordination with circuit breakers
- **event-gateway**: Multi-topic event routing with transformation and filtering
- **data-validator**: Multi-engine validation (schema, quality, business rules)
- **flow-monitor**: End-to-end flow tracing with performance analytics
- **telemetry-daemon**: System metrics collection and alerting
- **transport-router**: File-based event transport with validation
- **reentry-engine**: Enhanced re-entry processing with decision client

**Infrastructure Services**:
- **Redis** (6379): Message bus for event-driven communication
- **PostgreSQL** (5432): Persistent data storage
- **Prometheus** (9090): Metrics collection and monitoring
- **Grafana** (3000): Monitoring dashboards and visualization

**Contract System**:
- **Centralized Schema Registry** (`contracts/`): JSON schemas, CSV formats, identifier specs
- **Shared Libraries** (`shared/reentry/`): Hybrid ID system, vocabulary management
- **Data Integrity**: Atomic write policies with checksums and sequence validation
- **Cross-Language Parity**: Python/MQL4 consistency for shared components

### Legacy System Components

**Unified Interface System**
- **launch_trading_system.py**: Main entry point with Excel-like tabbed GUI
- **AppController** (`core/app_controller.py`): Core application orchestration
- **Tab Architecture**: Dashboard, Live Trading, Price Feed, History, Status, Tools, Calendar, Settings

**Guardian Protection System** (`src/eafix/guardian/`)
- **Multi-Agent Architecture**: Risk, Market, System, Compliance, Execution, Learning agents
- **Constraint Engine**: DSL-based trading constraints with repository management
- **Gate System**: Broker connectivity, market quality, risk management, system health gates
- **Monitoring**: Real-time trading system monitoring with health checks

**Signal & Indicator Engine**
- **Friday Vol Signal** (`src/eafix/signals/friday_vol_signal.py`): Volatility-based trading signals
- **Advanced Indicators** (`src/eafix/indicators/advanced/`): Rate differential momentum, volatility spillover analysis
- **Currency Strength** (`src/eafix/currency_strength.py`): Multi-currency strength analysis
- **Conditional Signals** (`src/eafix/conditional_signals.py`): Logic-based signal generation
- **Technical Indicators** (`src/eafix/indicators/`): RSI, MACD, Stochastic, Z-Score strength indicators

**Institutional Positioning System**
- **CFTC COT Processor** (`src/eafix/positioning/cftc/cot_processor.py`): Institutional positioning analysis
- **Retail Sentiment** (`src/eafix/positioning/retail/sentiment_aggregator.py`): Multi-source retail sentiment
- **Positioning Ratio Index** (`src/eafix/positioning/positioning_ratio_index/`): Institutional vs retail divergence

**Enhanced GUI Controls**
- **Emergency Controls** (`src/eafix/gui/enhanced/emergency_controls.py`): System emergency operations
- **Monitoring Tiles** (`src/eafix/gui/enhanced/monitoring_tiles.py`): Real-time system health monitoring
- **Expiry Services** (`src/eafix/services/expiry_indicator_service.py`): Options expiry microstructure analysis

### Database Architecture

**Modern Microservices** (`eafix-modular/`):
- **PostgreSQL**: Primary database for persistent storage
- **Redis**: Message bus and caching layer
- **Contract-Driven**: Schema validation enforced at runtime
- **Atomic Operations**: CSV files with checksums and sequence validation
- **Data Integrity**: Comprehensive validation across schema, quality, and business rules

**Legacy System**:
- **Multi-Database System**: trading_system.db, huey_project_organizer.db
- **Automated Backups**: Timestamped backup files with versioning
- **Guardian Schema**: Advanced constraint and monitoring tables
- **APF Integration**: Process state management and audit trails

### Testing Architecture

**Modern Microservices** (`eafix-modular/`):
- **Poetry + Pytest**: Managed dependencies with `pyproject.toml` configuration
- **Contract Testing**: Comprehensive schema validation with golden fixtures
- **Integration Testing**: End-to-end pipeline testing with Docker Compose
- **Service-Level Testing**: Individual service health and API validation
- **Performance Testing**: Tick replay testing for latency and throughput
- **Cross-Language Parity**: Python/MQL4 shared library consistency validation
- **CI/CD Integration**: Automated testing, linting, type checking in pipeline

**Legacy System**:
- **Pytest Configuration**: `pytest.ini` with src/ pythonpath
- **Enhanced Testing Framework**: `tests/enhanced/` with parallel execution capabilities
- **Dual Import Support**: Tests work with both package imports and direct imports
- **Comprehensive Coverage**: Trading signals, currency strength, economic calendar, UI components, advanced indicators
- **APF Tests**: Process framework, guardian system, constraint validation
- **Parallel Test Execution**: 6 test categories running simultaneously with comprehensive reporting

## Development Patterns

### Modern Microservices Patterns (`eafix-modular/`)

**Service Architecture**:
```python
# FastAPI service structure
from fastapi import FastAPI
from pydantic import BaseSettings
import structlog

class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    log_level: str = "INFO"
    
    class Config:
        env_prefix = "SERVICE_"

app = FastAPI(title="Service Name")
logger = structlog.get_logger()

@app.get("/healthz")
async def health_check():
    return {"status": "healthy"}
```

**Event-Driven Communication**:
```python
# Redis pub/sub pattern
import redis.asyncio as redis

async def publish_event(channel: str, event_data: dict):
    redis_client = redis.from_url(settings.redis_url)
    await redis_client.publish(channel, json.dumps(event_data))

async def subscribe_to_events(channels: List[str]):
    redis_client = redis.from_url(settings.redis_url)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(*channels)
    async for message in pubsub.listen():
        if message["type"] == "message":
            await process_event(message["data"])
```

**Contract Validation**:
```python
# Using shared contract models
from contracts.models.price_tick import PriceTick
from shared.reentry.hybrid_id import compose, parse, validate_key

# Validate incoming data against schema
price_tick = PriceTick(**incoming_data)

# Hybrid ID operations
hybrid_id = compose('W1', 'QUICK', 'AT_EVENT', 'CAL8_USD_NFP_H', 'LONG', 1)
components = parse(hybrid_id)
is_valid = validate_key(hybrid_id)
```

**Service Structure Pattern**:
```
services/<service-name>/
├── src/                 # Core service logic
│   ├── main.py         # FastAPI application entry point
│   ├── config.py       # Pydantic settings with env override
│   ├── models.py       # Data models matching event schemas
│   ├── health.py       # Health check logic
│   └── metrics.py      # Prometheus metrics
├── adapters/           # External system interfaces
├── tests/             # Unit and integration tests
├── Dockerfile         # Container configuration
└── requirements.txt   # Service-specific dependencies
```

### Legacy System Patterns

### Import Patterns

**Modern Microservices** (`eafix-modular/`):
```python
# Service-specific imports
from src.main import app
from src.config import Settings
from src.models import PriceTick, Signal, OrderIntent
from src.health import check_redis_connection

# Contract models and validation
from contracts.models.price_tick import PriceTick
from contracts.models.signal import Signal
from contracts.events.execution_report import ExecutionReport

# Shared libraries
from shared.reentry.hybrid_id import compose, parse, validate_key
from shared.reentry.vocab import ReentryVocabulary
from shared.reentry.indicator_validator import IndicatorValidator

# Testing with pytest
from tests.conftest import redis_client, sample_price_tick
import pytest
import pytest_asyncio
```

**Legacy System**:
```python
# APF package imports (preferred for new code)
from eafix.signals import FridayVolSignal
from eafix.guardian.constraints import ConstraintRepository
from eafix.indicators.advanced.rate_differential import RateDifferentialMomentum
from eafix.positioning.cftc.cot_processor import CFTCCOTProcessor
from eafix.gui.enhanced.emergency_controls import EmergencyControlsPanel

# Legacy direct imports (existing codebase compatibility)
from signals.friday_vol_signal import FridayVolSignal
from core.constraint_repository import ConstraintRepository
from core.app_controller import AppController
from core.database_manager import DatabaseManager

# Test imports (pytest with src/ pythonpath)
from tests.conftest import temp_db, mock_mt4_client
import pytest

# Root-level imports for main components
from launch_trading_system import TradingSystemLauncher
from eafix_cli import main as cli_main
```

### Code Style Guidelines

**Modern Microservices** (`eafix-modular/`):
- **Python 3.11+** with full type hints (enforced by mypy)
- **FastAPI** with async/await patterns for all I/O operations  
- **Pydantic** models for data validation and settings
- **Structured logging** with contextual information (structlog)
- **Black + isort** for consistent code formatting
- **Pytest** with async testing and coverage reporting
- **Contract-driven development** with schema validation
- **Defensive posture**: Fail closed on data integrity errors

**Legacy System**:
- Use Python type hints where possible for new code
- Follow existing patterns for GUI components (tkinter-based)
- Maintain compatibility with Windows DDE integration
- Use logging for debugging instead of print statements
- Follow pytest conventions for test organization

### Configuration Files

**Modern Microservices** (`eafix-modular/`):
```bash
# Project configuration
pyproject.toml                          # Poetry dependencies and tool configuration
Makefile                                 # Production operations and development commands
deploy/compose/docker-compose.yml        # Docker Compose service orchestration
.pre-commit-config.yaml                  # Git hooks and code quality automation

# Service configuration
services/*/src/config.py                 # Pydantic settings with environment variables
contracts/schemas/json/*.json            # Event schema definitions
contracts/policies/*.md                  # Data integrity and atomic write policies
shared/reentry/vocab.py                  # Canonical vocabulary specifications

# Testing and validation
tests/contracts/fixtures/                # Golden test data for contract validation
ci/validate_schemas.py                   # Schema validation automation
scripts/replay/                          # Performance testing tools
```

**Legacy System**:
```bash
# Core configuration
settings.json                    # Main application settings (trading signals, DDE, UI)
pytest.ini                      # Test configuration with pythonpath
launch_gui.bat / launch_gui.sh   # Platform-specific launcher scripts

# Dependencies
mt4_dde_interface/requirements.txt   # Python dependencies (pywin32, numpy, pandas, matplotlib, etc.)

# Trading analysis results (auto-generated)
scan_results.json               # System scan results
issues_results.json             # Detected issues
validation_results.json         # Validation status
metrics_results.json            # Performance metrics
remediation_results.json        # Remediation actions
production_validation_*.log     # Production validation logs

# Parallel integration results (auto-generated)
parallel_integration_results.json          # Full integration results
PARALLEL_STREAMS_COMPLETION_SUMMARY.md     # Comprehensive completion report
```

### File Structure Overview

**Modern Microservices Architecture** (`eafix-modular/`):
```
eafix-modular/
├── services/                  # Microservices (12 total)
│   ├── data-ingestor/         # Price feed normalization (8081)
│   ├── indicator-engine/      # Technical indicator computation (8082)
│   ├── signal-generator/      # Trading signal generation (8083)
│   ├── risk-manager/          # Risk validation and position sizing (8084)
│   ├── execution-engine/      # Broker order execution (8085)
│   ├── calendar-ingestor/     # Economic calendar processing (8086)
│   ├── reentry-matrix-svc/    # Re-entry decision matrix (8087)
│   ├── reporter/              # Metrics and P&L analysis (8088)
│   ├── gui-gateway/           # API gateway for operator UI (8080)
│   ├── flow-orchestrator/     # Event-driven flow coordination
│   ├── event-gateway/         # Multi-topic event routing
│   ├── data-validator/        # Multi-engine data validation
│   ├── flow-monitor/          # End-to-end flow tracing
│   ├── telemetry-daemon/      # System metrics and alerting
│   ├── transport-router/      # File-based event transport
│   └── reentry-engine/        # Enhanced re-entry processing
├── contracts/                 # Centralized schema registry
│   ├── schemas/json/          # Event and API schemas
│   ├── schemas/csv/           # CSV format specifications
│   ├── policies/              # Data integrity policies
│   └── events/                # Event schema definitions
├── shared/                    # Cross-service shared libraries
│   └── reentry/               # Hybrid ID system and vocabulary
├── tests/                     # Integration and contract tests
│   ├── contracts/             # Schema validation tests
│   └── integration/           # End-to-end pipeline tests
├── deploy/                    # Deployment configurations
│   └── compose/               # Docker Compose files
├── scripts/                   # Automation and testing scripts
├── pyproject.toml             # Poetry dependencies and configuration
├── Makefile                   # Development and production commands
└── README.md                  # Microservices documentation
```

**Legacy Trading System** (Root Level):
```
Root Level (Legacy Trading System)
├── core/                      # Core business logic (AppController, DatabaseManager, etc.)
├── tabs/                      # GUI tab components for trading interface
├── mt4_dde_interface/         # MetaTrader 4 DDE integration layer
├── CLI_FILES/                 # Development framework and orchestration tools
├── tools/                     # Analysis and validation scripts
├── tests/                     # Comprehensive test suite (pytest configuration)
├── launch_trading_system.py   # Main unified launcher (Excel-like GUI)
├── eafix_cli.py               # CLI entry point
├── settings.json              # Main configuration file
├── pytest.ini                # Test configuration (pythonpath = src)
└── *.db                       # SQLite databases

src/eafix/ (Modern APF Package)
├── apps/                      # Application modules
│   ├── cli/                   # Command-line interface (typer-based)
│   ├── desktop/               # Desktop GUI application
│   └── service/               # Background services
├── guardian/                  # Multi-agent protection system
│   ├── agents/                # Risk, Market, System, Compliance agents
│   ├── constraints/           # Constraint engine and DSL
│   └── gates/                 # Gate system (connectivity, quality, risk)
├── signals/                   # Trading signal processing
├── indicators/                # Technical analysis indicators
├── system/                    # Core system components
└── packages/                  # APF framework packages
```

## Parallel Streams Integration (99% System Completion)

The system has been enhanced through parallel development streams achieving 99% completion:

### Stream Integration Components
- **Stream A**: Enhanced Testing Framework with parallel execution (25% completion gain)
- **Stream B**: Advanced Indicators including rate differential and volatility spillover (20% completion gain)
- **Stream C**: Data Pipelines & Positioning with CFTC COT and retail sentiment (20% completion gain)
- **Stream D**: GUI Enhancements with emergency controls and monitoring (15% completion gain)

### Integration Validation
```bash
# Validate all stream integration
python run_parallel_integration.py

# Check individual stream health
from src.eafix.integration.stream_integrator import StreamIntegrator
integrator = StreamIntegrator('.')
results = integrator.run_integration()
print(f"System readiness: {results['system_readiness']['percentage']}%")
```

### Advanced Features Available
- **41 Sophisticated Indicators** across 7 categories with institutional-grade analytics
- **CFTC COT Data Processing** for institutional positioning analysis with contrarian signals
- **Multi-Source Retail Sentiment** aggregation (OANDA, IG, DailyFX) with extremes detection
- **Emergency System Controls** for production operations (STOP/RESUME, pause decisions, flatten positions)
- **Comprehensive Health Monitoring** with 12 real-time monitoring tiles across 4 categories
- **Multi-Agent Development Framework** for cost-optimized AI-powered development orchestration
- **Unified CLI Tool System** with 40+ commands across 6 categories (trade, guardian, system, analyze, setup, apf)

## Guardian System Operations

### Constraint Management
```python
# Guardian constraint operations
from eafix.guardian.constraints import ConstraintRepository, ConstraintDSL

# Agent operations
from eafix.guardian.agents import (
    RiskAgent, MarketAgent, SystemAgent, 
    ComplianceAgent, ExecutionAgent, LearningAgent
)
```

### Gate System
- **Broker Connectivity Gate**: Connection health and failover
- **Market Quality Gate**: Spread, volume, volatility validation
- **Risk Management Gate**: Position limits, exposure controls
- **System Health Gate**: Performance, memory, connectivity monitoring

## Trading System Launch Sequence

1. **Dependency Check**: Validates required and optional modules
2. **Configuration Load**: Loads settings.json and application config
3. **Database Initialization**: Connects to trading databases
4. **Guardian Startup**: Initializes constraint repository and agents
5. **GUI Creation**: Launches unified Excel-like interface
6. **Tab Registration**: Creates Dashboard, Trading, Feed, History, Status, Tools, Calendar, Settings
7. **Background Services**: Starts update threads and monitoring systems

## MetaTrader 4 Integration

### Expert Advisors
- **HUEY_P_EA_ExecutionEngine_8.mq4**: Main execution engine
- **HUEY_P_EA_ThreeTier_Comm.mq4**: Communication layer
- **Compilation**: Use MetaTrader MetaEditor (F7)

### DDE Interface
- **launch_gui.bat/sh**: Auto-launches MT4 if `terminal.exe` found
- **Environment Variable**: `MT4_PATH` for custom MT4 installation path
- **Fallback Paths**: Common Windows MT4 installation locations

## Production Validation

### System Validation
```bash
# Run comprehensive production validation
python production_validation.py

# Output files:
# - production_validation_YYYYMMDD_HHMMSS.log
# - validation_results_YYYYMMDD_HHMMSS.json
```

### Database Management
- **SQLite databases**: trading_system.db, huey_project_organizer.db, e2e_trading.db, e2e_guardian.db
- **Automatic backups**: Generated with timestamp suffixes
- **Database validation**: Included in production validation scripts

## Development Dependencies

### Installation Commands
```bash
# Install core trading system dependencies
pip install -r mt4_dde_interface/requirements.txt

# Core dependencies from requirements.txt:
pip install pywin32>=306 numpy>=1.24.0 pandas>=2.0.0 matplotlib>=3.7.0 seaborn>=0.12.0 asyncio-mqtt>=0.13.0

# Optional testing and development tools
pip install pytest pytest-cov
```

### Key Dependencies
- **pywin32>=306**: Windows API integration for DDE communication with MetaTrader 4
- **numpy>=1.24.0**: Numerical computations for trading algorithms and signal processing
- **pandas>=2.0.0**: Data analysis, time series manipulation, and CSV processing
- **matplotlib>=3.7.0**: Chart generation and data visualization
- **seaborn>=0.12.0**: Statistical data visualization and plotting
- **asyncio-mqtt>=0.13.0**: Asynchronous MQTT client for real-time data feeds

### Built-in Modules Used
- **tkinter**: GUI framework for desktop interface (built into Python)
- **sqlite3**: Database operations and validation (built into Python)
- **json**: Configuration file handling (built into Python)
- **logging**: Application logging and debugging (built into Python)

## System Status and Readiness

**Current Architecture Status**:
- **Modern Microservices** (`eafix-modular/`): **Production Ready** with 12+ services, comprehensive testing, and container deployment
- **Legacy System**: 99% completion with parallel streams integration
- **Integration Score**: 100/100 
- **Last Updated**: September 2025 via parallel streams and microservices architecture

### Modern Microservices Features (2025)
- **Complete Event-Driven Architecture**: 12 microservices with Redis pub/sub messaging
- **Runtime Flow Integration**: Flow orchestration, event gateway, data validation, performance monitoring
- **Contract-Driven Development**: Centralized schema registry with validation automation
- **Production Operations**: Docker Compose, Kubernetes-ready, comprehensive monitoring
- **Shared Libraries**: Cross-service components with Python/MQL4 parity
- **Data Integrity**: Atomic write policies, checksums, sequence validation
- **Performance Testing**: Tick replay testing with latency and throughput analysis

### Legacy System Enhancements (2025)
- Parallel testing framework with 6 simultaneous test categories
- Advanced institutional indicators (rate differential, volatility spillover)  
- CFTC COT institutional positioning analysis with automated data fetching
- Multi-source retail sentiment aggregation and contrarian signal generation
- Emergency controls and comprehensive system health monitoring
- Options expiry microstructure analysis for enhanced signal timing

### Production Readiness

**Modern Microservices**:
- **Service Level Objectives**: 99.9% uptime, <100ms price feed latency, <500ms signal generation
- **Gap Management**: Active tracking with Risk Priority Numbers (RPN scoring)
- **Observability**: Structured logging, Prometheus metrics, Grafana dashboards
- **Data Integrity**: Contract validation, atomic operations, defensive posture

**Legacy System**:
This system provides a production-ready trading environment with comprehensive protection, analysis, and monitoring capabilities through the Guardian system and APF integration. The parallel streams integration has transformed it from a functional core (70%) to a comprehensive institutional-grade trading platform (99%).

The **dual architecture** provides both **battle-tested legacy capabilities** and **modern scalable microservices**, offering comprehensive trading system capabilities for development and production environments.