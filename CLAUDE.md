# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a live MetaTrader 4 terminal directory containing the deployed HUEY_P Trading System - a hybrid algorithmic trading platform combining MQL4 Expert Advisors with Python-based monitoring and management tools.

**Terminal ID**: `F2262CFAFF47C27887389DAB2852351A` (Forex.com Live Account)
**Core System**: HUEY_P Expert Advisor with Python Interface Bridge
**Architecture**: Multi-layered with MQL4 execution engine, C++ DLL bridge, and Python GUI interface

## Key Development Commands

### Python Interface Development
```bash
# Navigate to development environment
cd eafix

# Environment setup
python -m venv venv
venv\Scripts\activate  
pip install -r huey_requirements.txt

# Main applications
python huey_main.py                    # Primary trading interface with tabs
python tkinter_main_ui.py             # Alternative interface
python floating_timer_ui.py           # Minimal floating display

# Database operations
python init_database.py               # Initialize/reset database schema
python fix_database_schema.py         # Repair database issues
python test_database_operations.py    # Validate database functionality
```

### MQL4 Expert Advisor Development  
```bash
# Compilation (requires MetaTrader 4 MetaEditor)
# Use MetaEditor: File → Compile (F7) or Edit → Compile (Ctrl+F7)
# Source files: MQL4/Experts/HUEY_P_EA_ExecutionEngine_8.mq4

# Automated testing framework
.\eafix\run_mql4_tests.ps1                              # Full test suite
.\eafix\run_mql4_tests.ps1 -CompileOnly                 # Compilation validation only
.\eafix\run_mql4_tests.ps1 -RunTests -GenerateReport    # Complete testing with HTML report
.\eafix\run_mql4_tests.ps1 -CleanupAfter                # Auto-cleanup after tests
```

### DLL Communication Bridge
```bash
# Navigate to DLL source
cd eafix\MQL4_DLL_SocketBridge

# Build DLL (requires Visual Studio 2019+ and CMake)
build_dll.bat

# Manual build process
cmake .. -G "Visual Studio 17 2022" -A Win32
cmake --build . --config Release

# Test DLL functionality
python test_exports.py                # Validate DLL exports
python simple_test.py                 # Basic DLL communication test
```

### System Integration Testing
```bash
# Communication bridge validation
cd eafix
python test_ea_python_communication.py    # EA-Python bridge testing
python test_system_integration.py         # Full system integration tests  
python test_port_5555.py                 # Socket connectivity validation
python test_signal_processing.py          # Signal processing validation

# Performance and health monitoring
python simple_socket_test.py             # Basic socket performance test
.\bridge_diagnostic.ps1                  # Communication bridge diagnostics
.\emergency_bridge_recovery.ps1          # Emergency recovery procedures
```

## Architecture Overview

### Three-Layer Hybrid System

**Layer 1: MQL4 Execution Engine**
- **Primary EA**: `HUEY_P_EA_ExecutionEngine_8.mq4` (7000+ lines, class-based architecture)
- **Strategy**: Advanced straddle system with dynamic trailing stops and risk adaptation
- **State Machine**: IDLE → ORDERS_PLACED → TRADE_TRIGGERED → PAUSED transitions
- **Risk Management**: Circuit breakers, daily drawdown limits, correlation tracking

**Layer 2: C++ Communication Bridge**  
- **DLL**: `MQL4_DLL_SocketBridge.dll` (socket interface between MQL4 and Python)
- **Protocol**: Bidirectional messaging on ports 5555 (MQL4) ↔ 9999 (Python)
- **Fallback**: CSV-based communication when socket bridge unavailable
- **Message Types**: HEARTBEAT, STATUS_REQUEST/RESPONSE, TRADE_UPDATE, ERROR

**Layer 3: Python Management Interface**
- **Modular Architecture**: `core/` (business logic), `tabs/` (UI components), `widgets/` (reusable controls), `utils/` (helpers)
- **Database**: SQLite with automated backups and schema validation
- **Real-time Monitoring**: Live dashboard with connection health indicators
- **Advanced Analytics**: Trade history analysis, performance metrics, risk monitoring

### Multi-Mode Operation Support

**Full Integration Mode** (Production)
- EA: `AutonomousMode=true`, `EnableDLLSignals=true`
- Python: Real-time communication with live data streams
- Requires: Properly deployed `MQL4_DLL_SocketBridge.dll`

**Monitoring-Only Mode** (Fallback)
- EA: `AutonomousMode=true`, `EnableDLLSignals=false`
- Python: Analysis and monitoring without EA communication
- Use when: DLL deployment not feasible or during EA development

**CSV Signal Mode** (Alternative Communication)
- EA: `EnableCSVSignals=true`, `EnableDLLSignals=false`
- Communication via: `trading_signals.csv`, `trade_responses.csv`
- Use when: Socket communication unavailable

## Critical Configuration Management

### EA Configuration (MT4 Interface Parameters)
```mql4
// Core operation modes
bool AutonomousMode = true;              // Internal logic vs external signals
bool EnableDLLSignals = true;            // Socket communication with Python
bool EnableCSVSignals = false;           // File-based signal processing

// Advanced risk controls
double RiskPercent = 1.0;                // Position sizing (% of equity)
double MaxLotSize = 1.0;                 // Maximum position size cap
double SafeMarginPercentage = 50.0;      // Margin utilization threshold

// System debugging and validation
bool EnableAdvancedDebug = true;         // Enhanced logging system
bool EnableStateValidation = true;       // State machine integrity checks
bool EnablePortfolioRisk = true;         // Portfolio-wide risk monitoring
```

### Python Configuration (`eafix/huey_config.txt`)
YAML structure covering:
- **Application**: Window sizing, refresh rates, theme preferences
- **Database**: Connection pooling, backup intervals, timeout settings
- **EA Bridge**: Socket configuration, retry logic, heartbeat intervals
- **Alerts**: Profit/loss thresholds, drawdown warnings, system notifications
- **Logging**: Levels, file rotation, performance monitoring

### Database Schema Architecture
**Core Tables**:
- `trades` - Complete trade execution records with entry/exit data
- `signals` - External signal history and processing results
- `system_status` - Real-time system health and performance metrics
- `configuration` - Dynamic parameter storage and validation
- `audit_logs` - Comprehensive system activity tracking

## Development Constraints and Safety

### MQL4 Development Rules (CRITICAL)
- **NEVER rewrite entire EA** - modify only specific targeted sections
- **MQL4 syntax only** - NO MQL5 functions, structures, or keywords
- **MetaEditor compilation** - ONLY use MT4's built-in compiler (Ctrl+F7)
- **Parameter-driven features** - All new functionality controlled by input parameters
- **Backward compatibility** - Preserve ALL existing functionality and variable names

### Live Trading Environment Safety
- **Live Account Warning**: This terminal connects to a live trading account with real money
- **Pre-deployment Testing**: Always test EA changes in Strategy Tester or demo account first
- **Backup Requirements**: Backup EA settings and database before modifications
- **State Validation**: Enable `EnableStateValidation=true` for integrity checking
- **Circuit Breaker Respect**: Honor EA pause states and risk limit triggers

### File Access Patterns
- **Locked Files**: Log files may be locked during active EA execution
- **Real-time Updates**: Signal CSV files updated continuously during trading
- **UTF-16 Config Files**: MT4 configuration files use special encoding
- **Permission Requirements**: DLL deployment requires MT4 "Allow DLL imports" setting

## Core Class Architecture

### MQL4 EA Component Classes
- **StateManager**: Trading state machine and transition logic
- **SignalManager**: Multi-source signal processing and validation
- **RiskManager**: Position sizing, drawdown monitoring, portfolio exposure
- **LogManager**: Structured logging with error classification system
- **TradeManager**: Order execution, modification, and lifecycle management

### Python Core Classes
- **AppController** (`core/app_controller.py`): Main application orchestration
- **DatabaseManager** (`core/database_manager.py`): SQLite operations with connection pooling
- **EAConnector** (`core/ea_connector.py`): Socket communication with MT4 EA
- **DataModels** (`core/data_models.py`): Type-safe data structures

### Communication Protocol Structure
```python
# Message format for EA-Python communication
{
    "timestamp": "2025-08-16T10:30:00Z",
    "message_type": "TRADE_UPDATE|STATUS_REQUEST|ERROR|HEARTBEAT",
    "source": "EA|PYTHON",
    "data": { /* payload specific to message type */ },
    "session_id": "unique_session_identifier"
}
```

## Testing and Validation Framework

### Python Testing Suite
- **Integration Tests**: `test_system_integration.py` - Full system validation
- **Database Tests**: `test_database_operations.py` - SQLite operations validation
- **Communication Tests**: `test_ea_python_communication.py` - Bridge functionality
- **Component Tests**: Individual module testing (config, signals, indicators)

### MQL4 Testing Framework  
- **PowerShell Automation**: `run_mql4_tests.ps1` with compilation and execution validation
- **Test Discovery**: Automatic detection of `Test*.mq4` files in test directory
- **HTML Reporting**: Comprehensive test reports with error analysis
- **MT4 Integration**: Strategy Tester integration for backtesting validation

## System Monitoring and Recovery

### Health Monitoring Commands
```bash
# Real-time system health
cd eafix
python simple_socket_test.py             # Test socket connectivity
.\bridge_diagnostic.ps1                  # Comprehensive bridge diagnostics

# Database health checks
python test_database_operations.py       # Validate database integrity
ls Database/trading_system.backup_*.db   # Check automated backups

# EA log monitoring (if not locked)
cd MQL4/Files
tail -f HUEY_P_Log.txt                  # EA activity log
```

### Recovery Procedures
- **Database Recovery**: Use timestamped backups in `eafix/Database/`
- **Communication Recovery**: Run `emergency_bridge_recovery.ps1`
- **EA State Recovery**: Restart EA with `EnableStateValidation=true`
- **Python Interface Recovery**: Restart `huey_main.py` - automatic reconnection

## External Dependencies

### Required System Components
- **MetaTrader 4**: Live trading platform with DDE server enabled
- **Python 3.8+**: With packages from `huey_requirements.txt`
- **Visual Studio Build Tools**: For DLL compilation (cmake, MSVC compiler)
- **Windows Socket Libraries**: System DLLs (`wsock32.dll`, `ws2_32.dll`)

### Optional Enhancement Files
- **Economic Calendar**: `NewsCalendar.csv` for fundamental analysis integration
- **Time Filters**: `TimeFilters.csv` for trading session management
- **Signal Files**: `trading_signals.csv` for external signal input

## Production Deployment Status

✅ **Python Interface**: Production-ready with modular architecture  
✅ **MQL4 EA**: Deployed and active (7000+ lines, class-based)  
✅ **Database System**: SQLite with automated backups and validation  
✅ **Testing Framework**: PowerShell automation with HTML reporting  
⚠️ **Socket Bridge**: Requires DLL compilation and deployment  
✅ **CSV Fallback**: File-based communication alternative operational

This system represents an enterprise-grade automated trading platform with comprehensive risk management, real-time monitoring, and defensive security measures. All development must prioritize system stability and trading account protection.