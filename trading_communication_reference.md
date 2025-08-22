# Trading System Communication Reference

## System Architecture

### Core Components
- **Python Analytics Engine**: Market analysis and parameter calculation
- **Socket DLL**: Real-time communication bridge
- **MetaTrader EA**: Trade execution and parameter application
- **CSV Fallback**: Backup communication channel
- **Database Logger**: Parameter change audit trail

### Communication Flow
```
[Python Analytics] ←→ [Socket DLL] ←→ [MetaTrader EA]
       ↓                                    ↑
[CSV Files] ←-------- Fallback Channel ----┘
       ↓
[Database Logger]
```

## Communication Channels

### Primary Channel: Socket Communication

**Components:**
- `SocketDLL.dll` - Custom MT4/MT5 DLL for socket operations
- `socket_handler.py` - Python socket client
- `ea_socket_receiver.mq4/5` - EA socket event handler

**Advantages:**
- Low latency (~1-5ms)
- Bidirectional communication
- Real-time confirmation
- JSON message support

**Message Format:**
```json
{
    "action": "UPDATE_PARAMS",
    "timestamp": "2025-08-20T08:25:15",
    "symbol": "EURUSD",
    "parameters": {
        "risk_percent": 0.5,
        "stop_loss_pips": 20,
        "take_profit_pips": 40,
        "max_trades": 1,
        "strategy_id": 3
    },
    "trigger_reason": "HIGH_VOLATILITY_PRE_NEWS",
    "session_id": "sess_20250820_082515"
}
```

### Backup Channel: CSV File Communication

**Files:**
- `trading_signals.csv` - Signal transmission
- `trade_responses.csv` - EA responses
- `reentry_profile_template.csv` - Reentry parameters

**Polling Mechanism:**
- EA checks files every 2-5 seconds
- File timestamp validation
- Atomic file operations (write + rename)

## Key Files and Components

### Python Side

**Core Files:**
```
analytics_engine.py     # Main analysis engine
parameter_matrix.py     # Parameter selection logic
socket_client.py        # Socket communication
csv_handler.py          # Backup CSV operations
market_monitor.py       # Real-time data feeds
governance_validator.py # Parameter validation
```

**Configuration:**
```python
# config.py
SOCKET_CONFIG = {
    "host": "127.0.0.1",
    "port": 9090,
    "timeout": 5,
    "max_retries": 3
}

CSV_CONFIG = {
    "signals_path": "trading_signals.csv",
    "responses_path": "trade_responses.csv",
    "poll_interval": 2
}
```

### MetaTrader EA Side

**Core Files:**
```
MainEA.mq4/5           # Primary trading logic
SocketHandler.mqh      # Socket communication
ParameterManager.mqh   # Parameter validation/storage
StateManager.mqh       # Trading state management
CSVReader.mqh          # Backup CSV operations
```

**Global Variables:**
```cpp
// Parameter storage
string g_SocketParams[];
double g_RiskPercent = 1.0;
int g_StopLossPips = 30;
int g_TakeProfitPips = 60;
int g_MaxTrades = 3;
int g_StrategyID = 1;
```

### Data Files

**Input Files:**
- `economic_calendar.csv` - News events and impact levels
- `governance_checklist.csv` - Parameter validation rules
- `symbol_config.csv` - Symbol-specific settings

**Communication Files:**
- `trading_signals.csv` - Parameter updates from Python
- `trade_responses.csv` - EA confirmations and status
- `reentry_profile_template.csv` - Reentry logic parameters

**Output Files:**
- `parameter_log.csv` - Change audit trail
- `performance_metrics.csv` - System performance data

## Message Types and Formats

### Parameter Update (Python → EA)
```json
{
    "action": "UPDATE_PARAMS",
    "symbol": "EURUSD",
    "parameters": {
        "risk_percent": 0.8,
        "stop_loss_pips": 25,
        "take_profit_pips": 50,
        "max_trades": 2
    },
    "validation_hash": "abc123",
    "session_id": "sess_001"
}
```

### Trade Signal (Python → EA)
```json
{
    "action": "TRADE_SIGNAL",
    "symbol": "GBPUSD",
    "direction": "BUY",
    "lot_size": 0.1,
    "entry_price": 1.2650,
    "stop_loss": 1.2620,
    "take_profit": 1.2710,
    "confidence": 0.85
}
```

### Confirmation (EA → Python)
```json
{
    "status": "SUCCESS",
    "action": "UPDATE_PARAMS",
    "applied_parameters": {
        "risk_percent": 0.8,
        "stop_loss_pips": 25
    },
    "timestamp": "2025-08-20T08:25:16",
    "session_id": "sess_001"
}
```

### Error Response (EA → Python)
```json
{
    "status": "ERROR",
    "error_code": "VALIDATION_FAILED",
    "message": "Risk percentage exceeds maximum limit",
    "rejected_value": 3.5,
    "max_allowed": 2.0,
    "session_id": "sess_001"
}
```

## Parameter Validation

### Governance Rules (from governance_checklist.csv)
```
Control: RISK_LIMIT
Range: 0.1% - 2.0%
Enforcement: EA Input Validation
Failure Action: Reject with error

Control: STOP_LOSS_RANGE  
Range: 10 - 100 pips
Enforcement: Parameter Validation
Failure Action: Use default value

Control: MAX_TRADES
Range: 1 - 5 trades
Enforcement: Position Manager
Failure Action: Queue signal
```

### Validation Flow
```cpp
bool ValidateParameters(double risk, int sl, int tp) {
    // Risk validation
    if(risk < 0.001 || risk > 0.02) {
        LogError("Risk out of range: " + DoubleToString(risk));
        return false;
    }
    
    // Stop loss validation  
    if(sl < 10 || sl > 100) {
        LogError("SL out of range: " + IntegerToString(sl));
        return false;
    }
    
    // Risk/reward validation
    if(tp < sl * 1.0) {
        LogError("Invalid R:R ratio");
        return false;
    }
    
    return true;
}
```

## Error Handling and Fallbacks

### Connection Failure
1. Socket timeout detected
2. Switch to CSV communication
3. Log fallback event
4. Continue parameter updates via file polling

### Parameter Validation Failure
1. Reject invalid parameters
2. Send error response to Python
3. Maintain current parameters
4. Log validation failure

### File System Errors
1. Retry file operations (3 attempts)
2. Use backup file locations
3. Alert monitoring system
4. Maintain last known good state

## Monitoring and Logging

### Performance Metrics
- Socket latency measurements
- Parameter update frequency
- Validation failure rates
- Fallback activation events

### Audit Trail
- All parameter changes logged with timestamps
- Trigger reasons recorded
- Validation results stored
- Performance impact tracked

### Health Checks
```python
def system_health_check():
    return {
        "socket_status": check_socket_connection(),
        "csv_file_access": verify_file_permissions(),
        "ea_response_time": measure_ea_latency(),
        "parameter_sync": verify_parameter_consistency()
    }
```

## Configuration Management

### Environment Settings
```ini
[SOCKET]
HOST=127.0.0.1
PORT=9090
TIMEOUT=5000
BUFFER_SIZE=1024

[FILES]
SIGNALS_PATH=./data/trading_signals.csv
RESPONSES_PATH=./data/trade_responses.csv
LOG_PATH=./logs/parameter_changes.log

[VALIDATION]
MAX_RISK_PERCENT=2.0
MIN_STOP_LOSS=10
MAX_STOP_LOSS=100
```

### EA Input Parameters
```cpp
input string    SocketHost = "127.0.0.1";
input int       SocketPort = 9090;
input string    SignalsFile = "trading_signals.csv";
input bool      EnableSocketComm = true;
input bool      EnableCSVFallback = true;
input int       MaxRiskPercent = 200; // 2.0%
```

## Deployment Checklist

### Python Environment
- [ ] Install required packages (socket, json, pandas)
- [ ] Configure socket permissions
- [ ] Set up file access paths
- [ ] Initialize database connections

### MetaTrader Setup
- [ ] Install SocketDLL.dll in Libraries folder
- [ ] Enable DLL imports in EA settings
- [ ] Configure file access permissions
- [ ] Set up global variable access

### File System
- [ ] Create data directories
- [ ] Set appropriate file permissions
- [ ] Configure backup locations
- [ ] Test file read/write access

### Network
- [ ] Open required ports (9090)
- [ ] Configure firewall rules
- [ ] Test socket connectivity
- [ ] Verify localhost communication