The Complete Reentry Trading System- Technical Specification & Process Flow
System Architecture Overview
The reentry trading system operates as a deterministic finite state machine with three core components operating in synchronized orchestration:

Python Controller - Signal detection, matrix routing, and orchestration engine
MetaTrader EA - Trade execution, position management, and broker interface
Matrix Database - Decision rulebook containing 11,680+ predefined scenarios

Complete Atomic Process Flow with All Branches
PHASE 0: System Initialization & Bootstrap
0.000 → SYSTEM_START
│
├─[0.001] Load Configuration Files
│  ├─SUCCESS→ Load parameters.schema.json
│  │  ├─[0.001a] Validate JSON structure
│  │  ├─[0.001b] Check required fields: $id, $schema, definitions
│  │  └─[0.001c] Cache schema in memory
│  └─FAILURE→ Schema Loading Error
│     ├─[0.001d] Log error: "CRITICAL: Schema load failed"
│     ├─[0.001e] Attempt fallback to cached schema
│     │  ├─EXISTS→ Use cached version, log warning
│     │  └─NOT_EXISTS→ System halt with code E_INIT_001
│     └─[0.001f] Send alert to monitoring system
│
├─[0.002] Initialize File System
│  ├─[0.002a] Check directory structure
│  │  ├─Common\Files\reentry\bridge\
│  │  ├─Common\Files\reentry\logs\
│  │  ├─Common\Files\reentry\config\
│  │  └─Common\Files\reentry\data\
│  ├─[0.002b] Create missing directories
│  │  └─PERMISSION_ERROR→ 
│  │     ├─Retry with elevated permissions
│  │     └─FAIL→ Alert and fallback to temp directories
│  └─[0.002c] Set file permissions (read/write for system)
│
├─[0.003] Initialize Communication Channels
│  ├─[0.003a] Open CSV file handles
│  │  ├─trading_signals.csv (write mode, append)
│  │  ├─trade_responses.csv (read mode, tail)
│  │  └─parameter_log.csv (write mode, append)
│  ├─[0.003b] Handle file lock scenarios
│  │  ├─FILE_LOCKED→ 
│  │  │  ├─Wait 100ms, retry (max 10 attempts)
│  │  │  └─PERSISTENT_LOCK→ Kill orphaned processes
│  │  └─FILE_CORRUPTED→
│  │     ├─Backup corrupted file with timestamp
│  │     └─Create new file with headers
│  └─[0.003c] Set read offsets to EOF
│
├─[0.004] Load Matrix Database
│  ├─[0.004a] Read matrix_map.csv
│  │  ├─Validate CSV structure (3 columns minimum)
│  │  └─ERROR→ Use backup matrix or halt
│  ├─[0.004b] Build hash-cache index
│  │  ├─Key: combination_id
│  │  ├─Value: {parameter_set_id, next_decision}
│  │  └─Collision handling: Log and use latest
│  └─[0.004c] Validate matrix completeness
│     ├─Check for required base combinations
│     └─MISSING→ Log gaps, use defaults
│
└─[0.005] Start Health Monitoring
   ├─[0.005a] Initialize timers
   │  ├─heartbeat_tx_interval = 30s
   │  ├─heartbeat_rx_timeout = 90s
   │  └─system_health_check = 60s
   └─[0.005b] Start background threads
      ├─Thread 1: Heartbeat sender
      ├─Thread 2: Response monitor
      └─Thread 3: Resource cleanup
PHASE 1: Economic Calendar Processing & Signal Generation
1.000 → CALENDAR_SCAN_START (runs every 60 seconds)
│
├─[1.001] File Discovery
│  ├─[1.001a] Scan %USERPROFILE%\Downloads
│  │  ├─Pattern: economic_calendar*.{csv,xlsx,xls}
│  │  └─NO_FILES→ 
│  │     ├─Check alternative directories
│  │     └─Wait for next scan cycle
│  ├─[1.001b] File validation
│  │  ├─Check file size (>0, <100MB)
│  │  ├─Check modification time (<24 hours old)
│  │  └─INVALID→ Archive and skip
│  └─[1.001c] Lock file for processing
│
├─[1.002] File Processing
│  ├─[1.002a] Copy to data\ with timestamp
│  │  └─COPY_FAIL→ 
│  │     ├─Check disk space
│  │     └─Use in-place processing
│  ├─[1.002b] Compute SHA-256 hash
│  ├─[1.002c] Compare with last processed
│  │  └─DUPLICATE→ Skip processing
│  └─[1.002d] Parse file format
│     ├─CSV→ Use csv.DictReader
│     ├─XLSX→ Use openpyxl
│     └─PARSE_ERROR→ 
│        ├─Try alternative encodings
│        └─Manual intervention required
│
├─[1.003] Data Transformation
│  ├─[1.003a] Normalize columns
│  │  ├─Map source columns to standard
│  │  ├─Handle missing fields with defaults
│  │  └─Validate data types
│  ├─[1.003b] Filter by impact
│  │  ├─Keep: HIGH, MED
│  │  ├─Drop: LOW, HOLIDAY, TENTATIVE
│  │  └─Log filtered count
│  └─[1.003c] Time zone conversion
│     ├─Convert all to UTC
│     └─Handle DST transitions
│
├─[1.004] Event Enrichment
│  ├─[1.004a] Add recurring events
│  │  ├─EQUITY_OPEN_USA (14:30 UTC daily)
│  │  ├─EQUITY_OPEN_EU (08:00 UTC daily)
│  │  ├─EQUITY_OPEN_ASIA (00:00 UTC daily)
│  │  └─Session overlaps
│  ├─[1.004b] Generate anticipation events
│  │  ├─For each HIGH impact:
│  │  │  ├─ANTICIPATION_8HR at T-480min
│  │  │  └─ANTICIPATION_1HR at T-60min
│  │  └─For each MED impact:
│  │     └─ANTICIPATION_1HR at T-60min only
│  └─[1.004c] Deduplicate events
│     └─Keep earliest if conflicts
│
└─[1.005] Calendar Activation
   ├─[1.005a] Write economic_calendar.csv
   │  └─Use atomic rename operation
   ├─[1.005b] Update memory index
   └─[1.005c] Broadcast update notification
PHASE 2: Signal Detection & Debouncing
2.000 → SIGNAL_DETECTION_LOOP (runs every 100ms)
│
├─[2.001] Time Window Analysis
│  ├─[2.001a] Get current UTC time
│  ├─[2.001b] Define detection windows
│  │  ├─IMMEDIATE: now to now+5min
│  │  ├─SHORT: now+5min to now+15min
│  │  ├─LONG: now+15min to now+60min
│  │  └─EXTENDED: now+60min to now+480min
│  └─[2.001c] Query calendar index
│     └─Returns: List of upcoming events
│
├─[2.002] Signal Candidate Generation
│  ├─[2.002a] Economic signals
│  │  ├─ECO_HIGH from high impact events
│  │  ├─ECO_MED from medium impact events
│  │  └─Check news blackout periods
│  ├─[2.002b] Anticipation signals
│  │  ├─ANTICIPATION_8HR (8 hours before)
│  │  └─ANTICIPATION_1HR (1 hour before)
│  ├─[2.002c] Session signals
│  │  ├─EQUITY_OPEN_USA
│  │  ├─EQUITY_OPEN_EU
│  │  └─EQUITY_OPEN_ASIA
│  └─[2.002d] Technical signals
│     └─ALL_INDICATORS (from external system)
│
├─[2.003] Debounce Logic
│  ├─[2.003a] Check recent signals (last 15min)
│  │  └─Key: (symbol, signal_type, event_id)
│  ├─[2.003b] Apply cooldown rules
│  │  ├─Same signal/symbol: 15min cooldown
│  │  ├─Any signal/symbol: 5min cooldown
│  │  └─OVERRIDE→ VIP events bypass cooldown
│  └─[2.003c] Check active positions
│     ├─If position open for symbol→ 
│     │  ├─Allow if chaining enabled
│     │  └─Skip if max positions reached
│     └─Global position limit check
│
├─[2.004] Context Building
│  ├─[2.004a] Determine generation
│  │  ├─O: Original (no parent trade)
│  │  ├─R1: First reentry
│  │  ├─R2: Second reentry
│  │  └─R3+: Terminal (not allowed)
│  ├─[2.004b] Calculate proximity
│  │  └─Time to nearest event determines bucket
│  ├─[2.004c] Set initial outcome
│  │  ├─Original trades: outcome=SKIP
│  │  └─Reentries: inherit from parent
│  └─[2.004d] Compute duration (reentries only)
│     ├─FLASH: 0-15 minutes
│     ├─QUICK: 16-60 minutes
│     ├─LONG: 61-480 minutes
│     └─EXTENDED: >480 minutes
│
└─[2.005] Signal Emission
   ├─[2.005a] Build combination_id
   │  ├─Grammar: gen:signal[:duration]:proximity:outcome
   │  └─Validate against regex pattern
   ├─[2.005b] Check signal gates
   │  ├─Time of day restrictions
   │  ├─Day of week restrictions
   │  └─Holiday calendar check
   └─[2.005c] Queue for processing
      └─Priority: VIP > HIGH > MED > LOW
PHASE 3: Matrix Resolution & Parameter Loading
3.000 → MATRIX_LOOKUP_START
│
├─[3.001] Primary Lookup
│  ├─[3.001a] Hash combination_id
│  ├─[3.001b] Query matrix_map cache
│  │  ├─FOUND→ Extract parameter_set_id
│  │  └─NOT_FOUND→ Fallback logic
│  └─[3.001c] Check next_decision field
│     ├─CONTINUE→ Proceed to parameter loading
│     └─END_TRADING→ Terminal state
│
├─[3.002] Fallback Hierarchy
│  ├─[3.002a] Try wildcard patterns
│  │  ├─Replace outcome with *
│  │  ├─Replace duration with *
│  │  └─Replace signal with category
│  ├─[3.002b] Try parent combinations
│  │  └─Strip components right-to-left
│  └─[3.002c] Use absolute default
│     └─parameter_set_id = PS-default
│
├─[3.003] Parameter Set Loading
│  ├─[3.003a] Load from parameters.json
│  │  └─FILE_ERROR→ Use cached version
│  ├─[3.003b] Find parameter_set by ID
│  │  └─NOT_FOUND→ Use template default
│  └─[3.003c] Clone for modification
│
├─[3.004] Dynamic Overlays
│  ├─[3.004a] Symbol-specific adjustments
│  │  ├─Spread multipliers for exotics
│  │  ├─Pip value corrections
│  │  └─Broker-specific tweaks
│  ├─[3.004b] Session overlays
│  │  ├─Asian session: reduce distances
│  │  ├─London open: increase ranges
│  │  └─NY session: standard ranges
│  ├─[3.004c] Volatility adjustments
│  │  ├─Query recent ATR
│  │  ├─Apply volatility multiplier
│  │  └─Cap at max thresholds
│  └─[3.004d] Risk scaling
│     ├─Account equity check
│     ├─Drawdown adjustment
│     └─Correlation risk (multi-pair)
│
└─[3.005] Validation Pipeline
   ├─[3.005a] Schema validation
   │  ├─Check required fields
   │  ├─Validate data types
   │  └─Range checking
   ├─[3.005b] Business rules
   │  ├─Risk ≤ 3.5% hard cap
   │  ├─TP > SL for fixed methods
   │  └─Logical consistency
   └─[3.005c] Broker compatibility
      ├─Minimum lot sizes
      ├─Tick size compliance
      └─Symbol availability
PHASE 4: Bridge Communication (Python → EA)
4.000 → SIGNAL_TRANSMISSION_START
│
├─[4.001] Message Construction
│  ├─[4.001a] Build UPDATE_PARAMS message
│  │  ├─version: "3.0"
│  │  ├─timestamp_utc: ISO-8601
│  │  ├─symbol: normalized pair
│  │  ├─combination_id: full context
│  │  ├─action: "UPDATE_PARAMS"
│  │  ├─parameter_set_id: reference
│  │  ├─json_payload_sha256: checksum
│  │  └─json_payload: full parameters
│  └─[4.001b] Compress if > 64KB
│     └─Use gzip, set compression flag
│
├─[4.002] Write Operations
│  ├─[4.002a] Acquire file lock
│  │  └─TIMEOUT→ Force unlock and retry
│  ├─[4.002b] Write to temp file first
│  ├─[4.002c] Fsync to ensure disk write
│  ├─[4.002d] Atomic rename to target
│  └─[4.002e] Release file lock
│
├─[4.003] Signal Triggering
│  ├─[4.003a] Evaluate entry conditions
│  │  ├─Immediate entry signals
│  │  ├─Delayed entry signals
│  │  └─Conditional entry signals
│  ├─[4.003b] Build TRADE_SIGNAL message
│  │  └─Include signal context
│  └─[4.003c] Append to CSV
│
└─[4.004] Response Monitoring Setup
   ├─[4.004a] Start acknowledgment timer
   │  ├─Timeout: 10 seconds
   │  └─Retry count: 3
   ├─[4.004b] Register callback handlers
   └─[4.004c] Log transmission event
PHASE 5: EA Reception & Validation
5.000 → EA_MESSAGE_PROCESSING
│
├─[5.001] File Monitoring
│  ├─[5.001a] Poll trading_signals.csv
│  │  ├─Interval: 100ms active, 2s idle
│  │  └─Use file change notification API
│  ├─[5.001b] Detect new lines
│  │  ├─Compare file size
│  │  └─Read from last offset
│  └─[5.001c] Parse CSV row
│     └─ERROR→ Log and skip row
│
├─[5.002] Message Validation
│  ├─[5.002a] Version check
│  │  ├─v3.0→ Current protocol
│  │  ├─v2.x→ Legacy adapter
│  │  └─Unknown→ REJECT_SET(E0000)
│  ├─[5.002b] Checksum verification
│  │  ├─Compute SHA-256
│  │  ├─Compare with provided
│  │  └─MISMATCH→ Request retransmit
│  └─[5.002c] Symbol validation
│     ├─Check if tradeable
│     ├─Market hours check
│     └─Spread threshold check
│
├─[5.003] Parameter Validation
│  ├─[5.003a] Schema compliance
│  │  ├─Parse JSON payload
│  │  ├─Validate against schema
│  │  └─INVALID→ REJECT_SET(E1000)
│  ├─[5.003b] Risk validation
│  │  ├─Calculate position size
│  │  ├─Check risk percentage ≤ 3.5%
│  │  └─EXCEED→ REJECT_SET(E1001)
│  ├─[5.003c] Stop/Target validation
│  │  ├─Minimum distance from market
│  │  ├─TP > SL for winners
│  │  └─INVALID→ REJECT_SET(E1012)
│  └─[5.003d] Account validation
│     ├─Sufficient margin
│     ├─Max positions check
│     └─Daily loss limit check
│
└─[5.004] State Update
   ├─[5.004a] Store parameters
   │  └─Key: (symbol, combination_id)
   ├─[5.004b] Update EA state
   │  ├─IDLE→ PARAMS_LOADED
   │  └─Log state transition
   └─[5.004c] Send acknowledgment
      └─ACK_UPDATE or REJECT_SET
PHASE 6: Trade Execution
6.000 → TRADE_EXECUTION_START
│
├─[6.001] Pre-Flight Checks
│  ├─[6.001a] News embargo check
│  │  ├─eco_cutoff_minutes_before
│  │  ├─eco_cutoff_minutes_after
│  │  └─BLOCKED→ REJECT_TRADE(E1040)
│  ├─[6.001b] Spread check
│  │  ├─Current vs max_spread_pips
│  │  └─EXCEED→ Wait or reject
│  ├─[6.001c] Connection check
│  │  ├─Broker connection status
│  │  └─OFFLINE→ Queue for retry
│  └─[6.001d] Account check
│     ├─Free margin available
│     └─Position limit check
│
├─[6.002] Lot Size Calculation
│  ├─[6.002a] Get account currency
│  ├─[6.002b] Calculate pip value
│  │  ├─Standard pairs: 10 units
│  │  ├─JPY pairs: 1000 units
│  │  └─Exotic adjustments
│  ├─[6.002c] Apply risk formula
│  │  └─Lots = (Risk% × Balance) / (SL_pips × PipValue)
│  └─[6.002d] Round to broker step
│     ├─Micro lots: 0.01
│     ├─Mini lots: 0.1
│     └─Standard lots: 1.0
│
├─[6.003] Order Placement
│  ├─MARKET Orders
│  │  ├─[6.003a] Get current price
│  │  ├─[6.003b] Check slippage
│  │  │  └─EXCEED→ Retry with new price
│  │  ├─[6.003c] Send OrderSend()
│  │  └─[6.003d] Handle requotes
│  ├─PENDING Orders (Straddle)
│  │  ├─[6.003e] Calculate entry levels
│  │  │  ├─BUY_STOP = Ask + distance
│  │  │  └─SELL_STOP = Bid - distance
│  │  ├─[6.003f] Place both orders
│  │  └─[6.003g] Link orders (OCO)
│  └─Order Failures
│     ├─[6.003h] Retry logic
│     │  ├─Max attempts: order_retry_attempts
│     │  ├─Delay: order_retry_delay_ms
│     │  └─Exponential backoff
│     └─[6.003i] Final failure
│        └─REJECT_TRADE(E1050)
│
└─[6.004] Post-Execution
   ├─[6.004a] Capture order IDs
   ├─[6.004b] Set EA state
   │  └─ORDERS_PLACED or TRADE_TRIGGERED
   ├─[6.004c] Start monitors
   │  ├─Trailing stop monitor
   │  ├─Timeout monitor
   │  └─News monitor
   └─[6.004d] Send confirmation
      └─ACK_TRADE with order details
PHASE 7: Position Management
7.000 → POSITION_MONITORING_LOOP
│
├─[7.001] Straddle Management
│  ├─[7.001a] Monitor pending orders
│  │  ├─Check if triggered
│  │  └─Update state on trigger
│  ├─[7.001b] OCO cancellation
│  │  ├─If one side fills→
│  │  ├─Cancel opposite pending
│  │  └─Log cancellation
│  └─[7.001c] Timeout handling
│     ├─Check pending_order_timeout_min
│     ├─Delete expired pendings
│     └─Send CANCELLED response
│
├─[7.002] Active Position Management
│  ├─[7.002a] Trailing stop logic
│  │  ├─FIXED trailing
│  │  │  ├─Trail by fixed pips
│  │  │  └─Only trail profits
│  │  ├─ATR trailing
│  │  │  ├─Calculate current ATR
│  │  │  └─Trail by ATR multiple
│  │  └─PERCENT trailing
│  │     └─Trail by profit percentage
│  ├─[7.002b] Breakeven logic
│  │  ├─Check if in profit ≥ BE pips
│  │  ├─Move SL to entry + 1
│  │  └─Lock in commission coverage
│  └─[7.002c] Emergency stop
│     ├─Max loss per position
│     ├─Time-based stops
│     └─Correlation stops
│
├─[7.003] Exit Detection
│  ├─[7.003a] Monitor OrderClose events
│  │  ├─Stop loss hit→ LOSS
│  │  ├─Take profit hit→ WIN
│  │  ├─Manual close→ MANUAL
│  │  └─Timeout close→ TIMEOUT
│  ├─[7.003b] Calculate metrics
│  │  ├─Pips gained/lost
│  │  ├─Time in trade (minutes)
│  │  ├─Peak profit/drawdown
│  │  └─Slippage on exit
│  └─[7.003c] Categorize outcome
│     ├─1: Big loss (< -50 pips)
│     ├─2: Loss (-50 to -10)
│     ├─3: Small loss (-10 to -1)
│     ├─4: Breakeven (-1 to +1)
│     ├─5: Win (+1 to +50)
│     └─6: Big win (> +50)
│
└─[7.004] Exit Reporting
   ├─[7.004a] Build close message
   │  ├─Result: WIN/LOSS/BE
   │  ├─Pips: actual P/L
   │  ├─Minutes: duration
   │  └─Exit reason
   ├─[7.004b] Write to responses
   └─[7.004c] Update EA state
      └─TRADE_CLOSED→ IDLE
PHASE 8: Reentry Decision Engine
8.000 → REENTRY_EVALUATION_START
│
├─[8.001] Trade Outcome Processing
│  ├─[8.001a] Receive close notification
│  ├─[8.001b] Parse outcome details
│  │  ├─Extract pips
│  │  ├─Extract duration
│  │  └─Extract exit type
│  └─[8.001c] Validate outcome
│     └─Ensure all required fields
│
├─[8.002] Chain Context Building
│  ├─[8.002a] Retrieve chain history
│  │  ├─Original trade context
│  │  ├─Previous reentry contexts
│  │  └─Cumulative metrics
│  ├─[8.002b] Determine next generation
│  │  ├─O→R1 transition
│  │  ├─R1→R2 transition
│  │  └─R2→Terminal
│  └─[8.002c] Apply generation rules
│     ├─Max 2 reentries (R2 cap)
│     ├─Degrading risk per level
│     └─Tightening parameters
│
├─[8.003] Combination ID Construction
│  ├─[8.003a] For ECO signals
│  │  ├─Include duration category
│  │  └─Format: gen:signal:duration:proximity:outcome
│  ├─[8.003b] For non-ECO signals
│  │  ├─Exclude duration
│  │  └─Format: gen:signal:proximity:outcome
│  └─[8.003c] Special combinations
│     ├─ALL pattern matching
│     ├─Category wildcards
│     └─Override combinations
│
├─[8.004] Matrix Decision
│  ├─[8.004a] Query matrix_map
│  │  ├─Exact match lookup
│  │  └─Fallback patterns
│  ├─[8.004b] Evaluate decision
│  │  ├─CONTINUE→ Get new parameters
│  │  ├─END_TRADING→ Stop chain
│  │  └─PAUSE→ Delay reentry
│  └─[8.004c] Apply overrides
│     ├─Account state overrides
│     ├─Time-based overrides
│     └─Risk limit overrides
│
└─[8.005] Reentry Execution
   ├─[8.005a] If CONTINUE
   │  ├─Load new parameter set
   │  ├─Apply generation modifiers
   │  └─GOTO Phase 3 with new context
   ├─[8.005b] If END_TRADING
   │  ├─Mark chain complete
   │  ├─Log chain summary
   │  └─Clear chain context
   └─[8.005c] If PAUSE
      ├─Set timer for retry
      └─Maintain chain context
PHASE 9: Error Recovery & Resilience
9.000 → ERROR_HANDLING_FRAMEWORK
│
├─[9.001] Communication Failures
│  ├─[9.001a] Missing ACK timeout
│  │  ├─Retry transmission (3x)
│  │  ├─Use backup channel
│  │  └─Alert and manual intervention
│  ├─[9.001b] Corrupted messages
│  │  ├─Request retransmission
│  │  ├─Use error correction
│  │  └─Skip and continue
│  └─[9.001c] File lock issues
│     ├─Force unlock after timeout
│     ├─Use lock-free alternatives
│     └─Restart file handles
│
├─[9.002] Execution Failures
│  ├─[9.002a] Order rejections
│  │  ├─Invalid price: Requote
│  │  ├─No money: Reduce size
│  │  ├─Market closed: Queue
│  │  └─Symbol halted: Cancel
│  ├─[9.002b] Partial fills
│  │  ├─Accept partial
│  │  ├─Complete remainder
│  │  └─Cancel remainder
│  └─[9.002c] Slippage handling
│     ├─Accept if < threshold
│     ├─Reject if excessive
│     └─Adjust parameters
│
├─[9.003] System Failures
│  ├─[9.003a] Python crash recovery
│  │  ├─Persist state to disk
│  │  ├─Reload on restart
│  │  └─Resume from checkpoint
│  ├─[9.003b] EA crash recovery
│  │  ├─Detect via heartbeat
│  │  ├─Restart EA
│  │  └─Resync positions
│  └─[9.003c] Matrix corruption
│     ├─Detect via checksums
│     ├─Load backup matrix
│     └─Rebuild from source
│
└─[9.004] Monitoring & Alerting
   ├─[9.004a] Health checks
   │  ├─Heartbeat monitoring
   │  ├─Resource usage
   │  └─Performance metrics
   ├─[9.004b] Alert triggers
   │  ├─Critical errors
   │  ├─Unusual patterns
   │  └─Limit breaches
   └─[9.004c] Reporting
      ├─Real-time dashboards
      ├─Email notifications
      └─SMS for critical
PHASE 10: Audit & Compliance
10.000 → AUDIT_TRAIL_SYSTEM
│
├─[10.001] Transaction Logging
│  ├─Every parameter set loaded
│  ├─Every signal generated
│  ├─Every order placed
│  ├─Every position closed
│  └─Every error encountered
│
├─[10.002] Compliance Checks
│  ├─Risk limit enforcement
│  ├─Regulatory compliance
│  ├─Broker rules adherence
│  └─Internal policy checks
│
└─[10.003] Performance Analytics
   ├─Win/loss ratios by combination
   ├─Profitability by signal type
   ├─Reentry effectiveness metrics
   └─System optimization data
State Machine Definitions
EA States
IDLE → Waiting for parameters
PARAMS_LOADED → Parameters received, awaiting signal
ORDERS_PLACED → Pending orders active
TRADE_TRIGGERED → Position active
TRADE_CLOSED → Position closed, awaiting cleanup
ERROR → Error state requiring intervention
DISABLED → System disabled
Chain States
INACTIVE → No chain active
ORIGINAL_ACTIVE → Original trade running
REENTRY_1_ACTIVE → First reentry running
REENTRY_2_ACTIVE → Second reentry running
CHAIN_COMPLETE → Terminal state reached
CHAIN_PAUSED → Temporary pause in chain
Critical Integration Points
1. Synchronization Mechanisms

File-based locks with timeout recovery
Atomic operations using temp→rename pattern
Heartbeat protocol for liveness detection
Checksum validation for data integrity

2. Risk Management Layers

Parameter validation at multiple points
Hard-coded 3.5% risk limit enforced by EA
Position sizing with account percentage
Drawdown monitoring with circuit breakers

3. Recovery Mechanisms

State persistence across restarts
Checkpoint recovery for long operations
Automatic retry with exponential backoff
Fallback parameters for missing configs

4. Performance Optimizations

In-memory caching of matrix and parameters
Lazy loading of large datasets
Batch processing of multiple signals
Async I/O for file operations

Matrix Grammar Specification
Combination ID Format
generation:signal_type[:duration]:proximity:outcome

Where:
- generation ∈ {O, R1, R2}
- signal_type ∈ {ECO_HIGH, ECO_MED, ANTICIPATION_1HR, ANTICIPATION_8HR, 
                 EQUITY_OPEN_USA, EQUITY_OPEN_EU, EQUITY_OPEN_ASIA, 
                 ALL_INDICATORS}
- duration ∈ {FLASH, QUICK, LONG, EXTENDED} (ECO signals only)
- proximity ∈ {IMMEDIATE, SHORT, LONG, EXTENDED}
- outcome ∈ {1, 2, 3, 4, 5, 6, SKIP, WIN, LOSS, BE}
Matrix Coverage

Total combinations: ~11,680 per currency pair
Supported pairs: 20 major and minor pairs
Default fallbacks: Every path has a default
Override capability: VIP combinations for special events

System Boundaries & Limits
Performance Limits

Max signals/second: 10
Max positions: 10 concurrent
Max reentries: 2 (R2 terminal)
Max risk: 3.5% per position

Time Constraints

Signal detection: 100ms cycle
EA response: 10 second timeout
Heartbeat: 30 second interval
File polling: 100ms active, 2s idle

Resource Limits

Memory: 2GB Python, 512MB EA
Disk: 10GB for logs/data
CPU: 4 cores recommended
Network: 10 Mbps minimum

Failure Modes & Mitigations
Critical Failures

Complete matrix corruption → Load backup, alert operator
Broker connection loss → Pause trading, attempt reconnect
Account margin call → Emergency close all, disable system
Schema version mismatch → Compatibility mode or halt

Degraded Operations

Slow file I/O → Increase timeouts, reduce frequency
High CPU usage → Disable non-critical features
Network latency → Increase slippage tolerance
Missing heartbeats → Switch to degraded monitoring

Conclusion
This reentry trading system represents a complete automated trading solution with:

Deterministic behavior through the matrix system
Robust error handling at every level
Complete audit trail for compliance
Recursive reentry logic for trade chains
Multiple safety mechanisms for risk control

The system operates as a synchronized state machine ensuring consistent, predictable, and traceable execution of trading strategies while maintaining strict risk controls and comprehensive error recovery capabilities.