# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a comprehensive trading system with dual architecture combining traditional trading tools with the Atomic Process Framework (APF). It includes MetaTrader 4 integration, signal processing, constraint-based protection systems, and a unified desktop interface.

**Architecture**: Hybrid system with legacy trading components and modern APF integration
**Focus**: Production trading system with Excel-like GUI, Guardian protection, and comprehensive analysis tools

## Key Development Commands

### Main Application Launch
```bash
# Primary system launcher (unified Excel-like interface)
python launch_trading_system.py

# APF desktop application
python -m eafix.apps.desktop.main

# Alternative launcher scripts
launch_gui.bat    # Windows
launch_gui.sh     # Unix/Linux
```

### Testing Framework
```bash
# Main test suite (pytest configured with src/ pythonpath)
pytest -q

# Run specific test categories
pytest tests/test_friday_vol_signal.py
pytest tests/test_currency_strength.py
pytest tests/test_conditional_signals.py
pytest tests/test_economic_calendar.py

# Run tests with full output
pytest -v tests/
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

### APF Commands
```bash
# APF CLI operations
python -m eafix.apps.cli.apf export   # Export process definitions
python -m eafix.apps.cli.apf validate # Validate process schemas
python -m eafix.apps.cli.apf seq      # Sequence management
```

## Architecture Overview

### Dual Architecture System

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

### Key Components

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
- **Currency Strength** (`src/eafix/currency_strength.py`): Multi-currency strength analysis
- **Conditional Signals** (`src/eafix/conditional_signals.py`): Logic-based signal generation
- **Technical Indicators** (`src/eafix/indicators/`): RSI, MACD, Stochastic, Z-Score strength indicators

### Database Architecture
- **Multi-Database System**: trading_system.db, huey_project_organizer.db
- **Automated Backups**: Timestamped backup files with versioning
- **Guardian Schema**: Advanced constraint and monitoring tables
- **APF Integration**: Process state management and audit trails

### Testing Architecture
- **Pytest Configuration**: `pytest.ini` with src/ pythonpath
- **Dual Import Support**: Tests work with both package imports and direct imports
- **Comprehensive Coverage**: Trading signals, currency strength, economic calendar, UI components
- **APF Tests**: Process framework, guardian system, constraint validation

## Development Patterns

### Import Patterns
```python
# APF package imports (preferred)
from eafix.signals import FridayVolSignal
from eafix.guardian.constraints import ConstraintRepository

# Legacy direct imports (fallback)
from signals.friday_vol_signal import FridayVolSignal
from core.constraint_repository import ConstraintRepository
```

### Configuration Files
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
```

### File Structure Patterns
```
Root Level (Legacy)              # Original trading system components
├── core/                       # Core business logic
├── tabs/                       # GUI tab components  
├── mt4_dde_interface/         # MT4 DDE integration
├── launch_trading_system.py   # Main unified launcher

src/eafix/ (APF)               # Modern package structure
├── apps/                      # CLI, desktop, service apps
├── guardian/                  # Protection system
├── signals/                   # Trading signals
├── indicators/                # Technical indicators
└── packages/                  # APF core packages

tests/                         # Unified test suite
tools/                         # Analysis and validation tools
docs/                          # Comprehensive documentation
```

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

### Python Requirements
- **pywin32>=306**: Windows API integration for DDE
- **numpy>=1.24.0**: Numerical computations for trading algorithms
- **pandas>=2.0.0**: Data analysis and manipulation
- **matplotlib>=3.7.0**: Chart generation and visualization
- **seaborn>=0.12.0**: Statistical data visualization
- **asyncio-mqtt>=0.13.0**: Asynchronous MQTT client

### Development Tools
- **pytest**: Testing framework with custom configuration
- **sqlite3**: Database operations and validation
- **tkinter**: GUI framework for desktop interface

This system provides a production-ready trading environment with comprehensive protection, analysis, and monitoring capabilities through the Guardian system and APF integration.