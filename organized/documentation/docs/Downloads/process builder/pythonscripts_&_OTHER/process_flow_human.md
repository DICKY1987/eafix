# Atomic Process Flow — Reentry Trading System (v3.1)

**Date:** 2025-08-22
**ID Conventions:** Format: SECTION.STEP (e.g., 1.001). Sub-processes: PREFIX.STEP (e.g., RC.001)

**Legend:** Each step is atomic (one action). Sub-processes are reusable components called from main steps.

---

## Sections
### 0.000 — System Bootstrap (One-Time on Service Start)
Initialize system components and validate configuration
**Actors:** PY · **Transport:** Filesystem

- **0.001** (PY) — Load Common\Files\reentry\config\parameters.schema.json into memory and validate file integrity.
  - Conditions: If schema file is missing or hash mismatch
  - GOTO: 11.010
  - Calls **FILE_VALIDATE**: Validate schema file integrity (existence/hash/age)
  - Validation: $id field present, $schema field present
  - Errors: E0000
  - Inputs: parameters_schema_path
  - Outputs: schema_content, schema_file_valid, schema_hash
- **0.002** (PY) — Validate schema self-integrity ($id, $schema fields present).
  - Conditions: If fail
  - Depends on: 0.001
  - GOTO: 11.010
  - Validation: $id field present, $schema field present
  - Inputs: schema_content
- **0.003** (PY) — Ensure directories exist: ...\bridge, ...\logs, ...\config, ...\data. Create if missing.
  - Depends on: 0.002

### 1.000 — Economic Calendar Ingestion (Hourly From Sunday 12:00 Local)
Ingest and process economic calendar data
**Actors:** PY, FS · **Transport:** CSV-only

- **1.001** (PY) — At scheduler tick, scan %USERPROFILE%\Downloads for newest economic_calendar*.csv/.xlsx.
  - Outputs: newest_calendar_path
- **1.002** (PY) — If none found GOTO 1.010. Else copy-as-new to data\economic_calendar_raw_YYYYMMDD_HHMMSS.ext (write→fsync→rename atomic).
  - Conditions: If none found
  - Depends on: 1.001
  - GOTO: 1.010
  - Calls **FILE_VALIDATE**: Validate calendar file before ingest
  - Inputs: newest_calendar_path
  - Outputs: ingested_calendar_path, calendar_file_valid, calendar_hash

### 3.000 — Matrix Routing & Parameter Resolution
Route signals and calculate parameters with risk management
**Actors:** PY · **Transport:** Memory

- **3.006** (PY) — Compute effective risk and position sizing via subprocess RISK_CALC.
  - Calls **RISK_CALC**: Calculate risk-adjusted position size
  - Validation: effective_risk <= 3.50
  - Errors: E1001
  - Inputs: global_risk_percent, volatility_adjustment, symbol_contract_info, account_balance, currency_conversion_rate
  - Outputs: calculated_risk, position_size, dollar_risk

### 11.000 — Error Handling & Termination
Fail-fast handling and logging
**Actors:** PY · **Transport:** Memory

- **11.010** (PY) — Abort initialization, log error, and raise E0000 if schema validation fails.
  - Conditions: If bootstrap validation fails
  - Errors: E0000
  - Inputs: error_detail


---

## Sub-process Library
### RISK_CALC — Risk Calculation and Position Sizing (v1.1)
Calculate effective risk percentage and convert to position size with validation
**Inputs:**
- `base_risk_percent` (number, required) — Base risk percentage (0.1-3.5)
- `volatility_multiplier` (number, required) — Volatility adjustment factor
- `symbol_info` (object, required) — Symbol contract specifications
- `account_balance` (number, required) — Current account balance
- `currency_conversion_rate` (number, optional) — USD conversion rate
**Outputs:**
- `effective_risk` (number, required) — Final calculated risk percentage
- `lot_size` (number, required) — Position size in lots
- `dollar_risk` (number, required) — Risk amount in account currency
- `validation_warnings` (array, optional) — Risk validation warnings
**Steps:**
- RC.001 (PY) — Apply volatility multiplier to base risk
- RC.002 (PY) — Enforce maximum risk cap of 3.50%
- RC.003 (PY) — Calculate dollar risk amount
- RC.004 (PY) — Convert to lot size using symbol contract specifications

### FILE_VALIDATE — File Integrity Validation (v1.0)
Validate file integrity with hash checking and atomic operations
**Inputs:**
- `file_path` (string, required) — Path to file to validate
- `expected_hash` (string, optional) — Expected SHA-256 hash
- `max_age_hours` (number, optional) — Maximum file age in hours
**Outputs:**
- `is_valid` (boolean, required) — File validation result
- `actual_hash` (string, required) — Computed file hash
- `file_size` (number, required) — File size in bytes
- `file_age_hours` (number, required) — File age in hours
**Steps:**
- FV.001 (PY) — Check file exists and compute basic metrics
- FV.002 (PY) — Compute SHA-256 hash of file content
- FV.003 (PY) — Compare with expected hash if provided
- FV.004 (PY) — Set validation failed for missing file

### ECO_PROCESS — Economic Calendar Processing (v1.0)
Transform raw economic calendar data into normalized trading signals
**Inputs:**
- `raw_calendar_data` (object, required) — Raw calendar data from source
- `impact_filter` (array, required) — Impact levels to include
- `currency_filter` (array, optional) — Currencies to process
**Outputs:**
- `normalized_events` (array, required) — Normalized calendar events
- `anticipation_events` (array, required) — Generated anticipation signals
- `processing_stats` (object, required) — Processing statistics
**Steps:**
- EP.001 (PY) — Filter events by impact and currency
- EP.002 (PY) — Normalize event data structure
- EP.003 (PY) — Generate anticipation events (1hr, 8hr before)
- EP.004 (PY) — Compute processing statistics

### ORDER_VALIDATE — Order Validation (v1.0)
Comprehensive validation of order parameters before submission
**Inputs:**
- `order_params` (object, required) — Complete order parameters
- `market_info` (object, required) — Current market state
- `account_info` (object, required) — Account constraints
**Outputs:**
- `is_valid` (boolean, required) — Order validation result
- `validation_errors` (array, optional) — List of validation errors
- `warnings` (array, optional) — Non-fatal warnings
- `adjusted_params` (object, required) — Adjusted order parameters
**Steps:**
- OV.001 (EA) — Validate order type and symbol
- OV.002 (EA) — Validate lot size against broker limits
- OV.003 (EA) — Validate SL/TP levels and distances
- OV.004 (EA) — Apply broker-specific adjustments


---

## Global I/O
**Global Inputs:**
- `economic_calendar_file` (string, required) — Path to economic calendar data
- `market_session` (string, required) — Current trading session (LONDON/NY/ASIA)
- `global_risk_percent` (number, required) — Base risk percentage for all trades
- `volatility_adjustment` (number, required) — Market volatility multiplier
- `system_parameters` (object, required) — Global system configuration
**Global Outputs:**
- `trade_signals` (array, required) — Generated trading signals ready for execution
- `system_health_status` (object, required) — Overall system health metrics
- `trade_results` (array, required) — Completed trade outcomes and statistics
- `error_log` (array, optional) — System errors and warnings

---

## File Paths
- **trading_signals**: `bridge\trading_signals.csv`
- **trade_responses**: `bridge\trade_responses.csv`
- **parameter_log**: `logs\parameter_log.csv`
- **economic_calendar**: `data\economic_calendar.csv`
- **matrix_map**: `config\matrix_map.csv`

---

## Metadata
**Actors:**
- PY: Python Service - Main orchestration and data processing
- EA: MT4 Expert Advisor - Trade execution and validation
- FS: Filesystem - File operations and data persistence
- BR: CSV Bridge - Inter-process communication
- TEST: QA Testing - Validation and test scenarios
**Error Codes:**
- E0000: Version mismatch between components or schema failure
- E1001: Risk limit exceeded (>3.50%)
- E1012: Take profit must be greater than stop loss
- E1020: ATR validation failed
- E1030: Maximum generation limit exceeded
- E1040: News cutoff time violation
- E1050: Order placement failed after retries
**SLA Categories:**
- fast: ≤50ms - Simple calculations and validations
- standard: ≤500ms - File operations and API calls
- complex: ≤2000ms - Complex calculations and transformations
- broker: ≤5000ms - Broker operations (network dependent)