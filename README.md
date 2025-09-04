# eafix - Trading System with APF Integration

This repository contains a comprehensive trading system combining traditional trading tools 
with the Atomic Process Framework (APF). It includes trading utilities, economic calendar 
processing, and a unified desktop interface for MetaTrader 4 integration.

## Features

- **Trading System Tools**: Placeholder utilities for early-stage pipeline development
- **APF Integration**: Process automation framework with diagnostics and validation
- **Desktop GUI**: Unified interface with MetaTrader 4 integration
- **Signal Processing**: Friday volatility signals and currency strength analytics
- **Guardian System**: Comprehensive constraint-based trading protection

## Project Structure

- `src/` – Application source code (`eafix` package and submodules)
- `tests/` – Unit tests and integration tests
- `tools/` – Trading analysis and validation tools
- `core/` – Core trading system components
- `tabs/` – GUI tab interfaces
- `organized/` – Cleaned repository contents
  - `main_applications/` – Entry point scripts
  - `configuration/` – JSON/YAML configuration files
  - `documentation/` – Project documentation and guides
  - `mql4_integration/` – MetaTrader 4 bridges and artifacts
  - `utilities/` – Helper scripts and modules
  - `archived/` – Legacy files and backups

## Quick Start

Run the test suite:
```bash
pytest -q
```

Launch the trading system:
```bash
python organized/main_applications/launch_trading_system.py
```

## Launching the Desktop GUI with MetaTrader 4

The desktop application automatically launches MetaTrader 4 if the `terminal.exe`
executable can be located. The launcher checks the `MT4_PATH` environment variable
first and falls back to common installation paths on Windows.

Helper scripts for desktop shortcuts (located in `organized/main_applications/`):

- `launch_gui.bat` – Windows batch file
- `launch_gui.sh` – POSIX shell script

Both scripts execute `python -m eafix.apps.desktop.main` which starts MetaTrader 4
(if available) and then the Python GUI.
