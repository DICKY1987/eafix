# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a trading system development repository containing Python-based trading tools, MetaTrader 4 Expert Advisors, and economic calendar processing utilities. The system includes placeholder trading infrastructure to enable early-stage pipeline development without requiring real trading infrastructure.

**Architecture**: Multi-component system with MQL4 Expert Advisors, Python interfaces, and database management
**Focus**: Development tools and testing frameworks for algorithmic trading systems

## Key Development Commands

### Python Development
```bash
# Navigate to repository
cd eafix

# Install dependencies for MT4 DDE interface
cd mt4_dde_interface
pip install -r requirements.txt

# Main application entry points
cd mt4_dde_interface
python run_application.py              # Main MT4 DDE interface application

# Economic calendar processing
cd "Economic calendar"
python simple_runner.py               # Basic economic calendar runner

# Database operations
python -c "from core.database_manager import DatabaseManager; db = DatabaseManager(); db.initialize_database()"
```

### Testing Framework
```bash
# Run main test suite
pytest -q

# Run specific test modules
pytest tests/test_calendar_processing.py
pytest tests/test_constraint_repository.py
pytest tests/test_friday_vol_indicator.py

# Run MT4 DDE interface tests
cd mt4_dde_interface/tests
python run_all_tests.py

# Individual MT4 DDE tests
python -m pytest test_dde_connection.py
python -m pytest test_currency_strength.py
python -m pytest test_indicators.py
```

### MQL4 Expert Advisor Development
```bash
# Main EA files for MetaTrader 4 compilation
# Use MetaEditor: File → Compile (F7)
# Source files:
# - HUEY_P_EA_ExecutionEngine_8.mq4
# - HUEY_P_EA_ThreeTier_Comm.mq4
```

### Trading Tools Validation
```bash
# Apply trading patches and validate configurations
cd tools
python apply_trading_patch.py
python run_trading_validation.py
```

## Architecture Overview

### Core Components

**Python Core** (`core/` directory)
- **AppController** (`app_controller.py`): Main application orchestration with tkinter GUI
- **DatabaseManager** (`database_manager.py`): SQLite database operations and schema management
- **EAConnector** (`ea_connector.py`): Communication interface with MetaTrader Expert Advisors
- **DataModels** (`data_models.py`): Type-safe data structures for trading data
- **ConstraintRepository** (`constraint_repository.py`): Trading constraint management system

**MT4 DDE Interface** (`mt4_dde_interface/` directory)
- **Main Application** (`run_application.py`): Primary interface for MT4 DDE communication
- **Currency Strength** (`src/currency_strength.py`): Currency strength analysis tools  
- **Indicators** (`src/indicators.py`): Technical indicator calculations
- **DDE Connection** (`src/dde_connection.py`): Dynamic Data Exchange with MetaTrader

**Tab-Based GUI** (`tabs/` directory)
- Modular tab system for different trading functionalities
- Live dashboard, trade history, system status, settings, and economic calendar tabs

### Database Architecture
- **SQLite-based**: Local database with automated schema management
- **Backup System**: Automated database backups with timestamp naming
- **Core Tables**: trades, signals, system_status, configuration, audit_logs

### Testing Framework
- **pytest**: Main testing framework with comprehensive test coverage
- **Component Tests**: Individual module testing for core components
- **Integration Tests**: Full system validation tests
- **MT4 Interface Tests**: Specialized tests for MetaTrader integration

## Development Guidelines

### Python Development
- **Dependencies**: Install from `mt4_dde_interface/requirements.txt`
- **Core Dependencies**: pywin32, numpy, pandas, matplotlib, seaborn, asyncio-mqtt
- **GUI Framework**: tkinter with ttk styling
- **Database**: SQLite with connection pooling and validation

### MQL4 Development
- **Compilation**: Use MetaTrader 4 MetaEditor (F7 or Ctrl+F7)
- **Syntax**: MQL4 only - no MQL5 functions or structures
- **Testing**: Use MetaTrader Strategy Tester for backtesting

### File Structure Patterns
```
core/                   # Business logic and core components
tabs/                   # GUI tab components
mt4_dde_interface/      # MT4 Dynamic Data Exchange interface
tests/                  # Test suite
tools/                  # Utility scripts and trading tools
indicators/             # Technical indicator implementations
signals/                # Trading signal processing
Database/               # SQLite databases and backups
```

## Key Configuration Files

### Dependencies
- `mt4_dde_interface/requirements.txt` - Python package dependencies

### Database Files
- `trading_system.db` - Main trading database
- `trading_system.backup_*.db` - Automated database backups
- `huey_project_organizer.db` - Project organization database

### Configuration Files
- `repo_ingester.config.json` - Repository ingestion configuration
- `repo_ingester.config.yaml` - Alternative YAML configuration format

## Testing and Validation

### Test Categories
1. **Core Component Tests**: Database, constraints, data models
2. **UI Component Tests**: Tab functionality and indicator validation  
3. **MT4 Interface Tests**: DDE connection, currency strength, indicators
4. **Integration Tests**: Full system workflow validation
5. **Trading Tool Tests**: Patch application and validation tools

### Test Execution
- **Primary Command**: `pytest -q` for main test suite
- **Specific Tests**: Target individual test files with `pytest tests/test_*.py`
- **MT4 Tests**: Run from `mt4_dde_interface/tests/` directory

## External Dependencies

### Required Components
- **Python 3.8+**: Core runtime environment
- **MetaTrader 4**: For MQL4 Expert Advisor execution (optional for development)
- **Windows**: Required for pywin32 DDE functionality

### Optional Components
- **SQLite Browser**: For database inspection and management
- **MetaTrader Strategy Tester**: For EA backtesting and validation

This repository provides a comprehensive development environment for algorithmic trading systems with focus on testing, validation, and modular architecture. The placeholder trading infrastructure enables development without requiring live trading connections.