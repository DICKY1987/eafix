# Reentry Trading System — Single Source of Truth (v3.0)

**Date:** 2025-08-20  
**Profile:** `CSV_ONLY` transport (no sockets)  
**Scope:** Executable parameter schema · Message & CSV contracts · Matrix ID grammar · EA validation checklist · Invariants & test cues

---

## 0) Purpose & Non‑Goals

**Purpose.** Provide a single, machine- and human-readable spec that Python, MT4 EA, and UI all obey. Everything here is normative.  
**Non‑Goals.** This doc doesn’t prescribe strategy logic or indicators; it constrains *interfaces, data, and validation* so implementations can vary without breaking contracts.

---

## 1) Executable Parameter Schema (YAML → JSON Schema)

> YAML is for readability; JSON Schema is for strict validation. The EA must treat schema violations as **REJECT_SET** events. All numeric units are in **account percent** (risk), **pips** (SL/TP), **minutes** (durations), or **ms** (delays) unless noted.

### 1.1 YAML (authoritative keys & types)
```yaml
version: 3.0
parameters:
  # ── Risk & sizing ──────────────────────────────────────────────
  global_risk_percent:        {type: number, min: 0.01, max: 3.50, required: true}
  risk_multiplier:            {type: number, min: 0.10, max: 3.00, default: 1.00}
  max_risk_cap_percent:       {type: number, const: 3.50}

  # ── Stop Loss (SL) ─────────────────────────────────────────────
  stop_loss_method:           {type: enum, values: [FIXED, ATR, PERCENT], required: true}
  stop_loss_pips:             {type: number, min: 5,  max: 1000, requires: {stop_loss_method: FIXED}}
  stop_loss_percent:          {type: number, min: 0.05, max: 10.0,  requires: {stop_loss_method: PERCENT}}
  sl_atr_multiple:            {type: number, min: 0.5, max: 10.0,  requires: {stop_loss_method: ATR}}
  sl_atr_period:              {type: integer, min: 5,  max: 200,   requires: {stop_loss_method: ATR}}
  sl_atr_timeframe:           {type: enum, values: [M1,M5,M15,M30,H1,H4,D1], requires: {stop_loss_method: ATR}}

  # ── Take Profit (TP) ───────────────────────────────────────────
  take_profit_method:         {type: enum, values: [FIXED, RR, ATR], required: true}
  take_profit_pips:           {type: number, min: 5,  max: 2000, requires: {take_profit_method: FIXED}}
  rr_target:                  {type: number, min: 0.10, max: 15.0, requires: {take_profit_method: RR}}
  tp_atr_multiple:            {type: number, min: 0.5, max: 20.0, requires: {take_profit_method: ATR}}
  tp_atr_period:              {type: integer, min: 5,  max: 200,   requires: {take_profit_method: ATR}}
  tp_atr_timeframe:           {type: enum, values: [M1,M5,M15,M30,H1,H4,D1], requires: {take_profit_method: ATR}}

  # ── Entry order & pending options ──────────────────────────────
  entry_order_type:           {type: enum, values: [MARKET, BUY_STOP_ONLY, SELL_STOP_ONLY, STRADDLE], required: true}
  market_slippage_tolerance:  {type: number, min: 0.0, max: 5.0, default: 0.5}   # pips
  order_retry_attempts:       {type: integer, min: 0, max: 10, default: 2}
  order_retry_delay_ms:       {type: integer, min: 0, max: 60000, default: 500}
  pending_order_timeout_min:  {type: integer, min: 1, max: 1440, default: 120}
  pending_price_method:       {type: enum, values: [FIXED, ATR, SUPPORT_RESISTANCE], default: FIXED}

  # ── Straddle (applies when entry_order_type=STRADDLE) ──────────
  straddle_buy_distance_pips: {type: number, min: 1, max: 500, requires: {entry_order_type: STRADDLE}}
  straddle_sell_distance_pips:{type: number, min: 1, max: 500, requires: {entry_order_type: STRADDLE}}
  straddle_auto_cancel_opposite: {type: boolean, default: true}

  # ── Confidence & volatility gates ──────────────────────────────
  min_signal_confidence:      {type: number, min: 0.0, max: 1.0, default: 0.0}
  enable_volatility_gate:     {type: boolean, default: false}
  atr_vol_threshold:          {type: number, min: 0.0, max: 1000.0, requires_if: {enable_volatility_gate: true}}
  atr_vol_period:             {type: integer, min: 5, max: 200, requires_if: {enable_volatility_gate: true}}
  atr_vol_timeframe:          {type: enum, values: [M1,M5,M15,M30,H1,H4,D1], requires_if: {enable_volatility_gate: true}}

  # ── Calendar & time filters ────────────────────────────────────
  eco_cutoff_minutes_before:  {type: integer, min: 0, max: 180, default: 10}
  eco_cutoff_minutes_after:   {type: integer, min: 0, max: 240, default: 10}
  allow_holiday_trading:      {type: boolean, default: false}

  # ── Trailing & breakeven (optional) ────────────────────────────
  trailing_stop_method:       {type: enum, values: [DISABLED, CONTINUOUS, STEPPED], default: DISABLED}
  trailing_initial_distance:  {type: number, min: 1, max: 1000, requires_if_any: {trailing_stop_method: [CONTINUOUS, STEPPED]}}
  trailing_step_size_pips:    {type: number, min: 1, max: 500, requires: {trailing_stop_method: STEPPED}}
  breakeven_trigger_pips:     {type: number, min: 1, max: 1000}
  breakeven_offset_pips:      {type: number, min: -50, max: 100}

  # ── Reentry chain controls ─────────────────────────────────────
  max_reentry_generation:     {type: enum, values: [O, R1, R2], default: R2}
  reentry_size_multiplier:    {type: number, min: 0.10, max: 3.00, default: 1.00}
  reentry_delay_seconds:      {type: integer, min: 0, max: 3600, default: 0}

  # ── Meta ───────────────────────────────────────────────────────
  parameter_set_id:           {type: string, regex: "^PS-[a-z0-9-]+$", required: true}
  description:                {type: string, max_len: 200}
```

### 1.2 JSON Schema (validator source of truth)
> Generate this mechanically from the YAML above. For brevity here, only the **top-level** is shown; the codegen must expand each field with `type`, `minimum`, `maximum`, `enum`, and conditional `allOf` clauses.
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "reentry_parameters.schema.json",
  "type": "object",
  "required": ["global_risk_percent", "stop_loss_method", "take_profit_method", "entry_order_type", "parameter_set_id"],
  "properties": {
    "global_risk_percent": {"type":"number","minimum":0.01,"maximum":3.5},
    "risk_multiplier": {"type":"number","minimum":0.1,"maximum":3.0,"default":1.0},
    "max_risk_cap_percent": {"type":"number","const":3.5},
    "stop_loss_method": {"type":"string","enum":["FIXED","ATR","PERCENT"]},
    "take_profit_method": {"type":"string","enum":["FIXED","RR","ATR"]},
    "entry_order_type": {"type":"string","enum":["MARKET","BUY_STOP_ONLY","SELL_STOP_ONLY","STRADDLE"]},
    "parameter_set_id": {"type":"string","pattern":"^PS-[a-z0-9-]+$"}
  },
  "additionalProperties": true
}
```

**Enforcement rule:** `effective_risk = min(global_risk_percent * risk_multiplier, max_risk_cap_percent)`; EA must compute size from `effective_risk` only (no direct lot inputs).

---

## 2) Message & CSV Contracts (CSV‑only Transport)

> All timestamps are **UTC ISO‑8601** with seconds. Files live under:  
**Python → MT4**: `Common\Files\reentry\bridge\trading_signals.csv`  
**MT4 → Python**: `Common\Files\reentry\bridge\trade_responses.csv`  
**EA Logs**: `Common\Files\reentry\logs\parameter_log.csv`

### 2.1 Atomic write requirement (producer side)
1. Write to `*.tmp` in same directory.  
2. Flush & fsync file handle.  
3. Rename `*.tmp` → target filename (atomic within volume).  
4. **Never** modify a file in place; always rewrite whole file.  
5. Files are **append‑only**; reader tracks `last_offset`.

### 2.2 `trading_signals.csv` (Python → EA)
```
# header
version,timestamp_utc,symbol,combination_id,action,parameter_set_id,json_payload_sha256,json_payload

# types
version: string  ("3.0")
timestamp_utc: string (ISO‑8601)
symbol: string (e.g., EURUSD)
combination_id: string (see §3)
action: enum (UPDATE_PARAMS | TRADE_SIGNAL | CANCEL_PENDING | HEARTBEAT)
parameter_set_id: string (PS-...)
json_payload_sha256: hex‑string of SHA‑256(json_payload)
json_payload: stringified JSON of parameters (must conform to §1)
```
**Notes**
- For `UPDATE_PARAMS`, `json_payload` contains the full parameter set.  
- For `TRADE_SIGNAL`, include `signal_context` keys (e.g., `"reason":"ECO_HIGH"`).  
- `HEARTBEAT` rows may omit `parameter_set_id` and `json_payload`.

### 2.3 `trade_responses.csv` (EA → Python)
```
# header
version,timestamp_utc,symbol,combination_id,action,status,ea_code,detail_json

# types
version: string  ("3.0")
timestamp_utc: string (ISO‑8601)
symbol: string
combination_id: string (echo from request if available)
action: enum (ACK_UPDATE | ACK_TRADE | REJECT_SET | REJECT_TRADE | CANCELLED | HEARTBEAT)
status: enum (OK | ERROR | WARNING)
ea_code: string (E1001, W2003, etc.)
detail_json: stringified JSON ({"message":"...","order_ids":[...]})
```

### 2.4 `parameter_log.csv` (EA log)
```
# header
version,timestamp_utc,symbol,parameter_set_id,effective_risk,sl,sl_units,tp,tp_units,entry_order_type,trail_method,breakeven,notes
```

---

## 3) Matrix ID Grammar (Deterministic Routing)

> The **combination_id** selects the parameter set and the next‑step decision. Duration applies **only** to ECO signals.

### 3.1 EBNF Grammar
```
combination_id := generation ":" signal [":" duration] ":" proximity ":" outcome

# generations
generation := "O" | "R1" | "R2"

# signals
signal := "ECO_HIGH" | "ECO_MED" | "ANTICIPATION_1HR" | "ANTICIPATION_8HR" |
          "EQUITY_OPEN_ASIA" | "EQUITY_OPEN_EUROPE" | "EQUITY_OPEN_USA" | "ALL_INDICATORS"

# duration (ECO_* only)
duration := "FLASH" | "QUICK" | "LONG" | "EXTENDED"

# proximity buckets
proximity := "IMMEDIATE" | "SHORT" | "LONG" | "EXTENDED"

# outcomes
outcome := "WIN" | "LOSS" | "BE" | "SKIP" | "REJECT" | "CANCEL"
```

### 3.2 Examples
- `O:ECO_HIGH:FLASH:IMMEDIATE:SKIP`  
- `R1:ALL_INDICATORS:LONG:LOSS` *(no duration segment)*  
- `R2:ECO_MED:QUICK:SHORT:WIN`

### 3.3 Mapping Contract
- Python maintains `matrix_map.csv` → `combination_id,parameter_set_id,next_decision`  
- The EA treats `parameter_set_id` as the sole source of runtime inputs (see §1).  
- **R2 is terminal**: EA must not generate further reentries beyond `R2`.

---

## 4) EA Validation Checklist (Pre‑Execution Gates)

> The EA must evaluate these checks **on every UPDATE_PARAMS** and **before every order action**. If a check fails, follow the Action column and log `ea_code`.

| Area | Rule | Enforcement Point | Action | ea_code |
|---|---|---|---|---|
| Risk | `effective_risk ≤ max_risk_cap_percent (3.50)` | On UPDATE_PARAMS | REJECT_SET | E1001 |
| SL/TP | If TP is FIXED: `take_profit_pips > stop_loss_pips` | Pre‑OrderSend | REJECT_SET | E1012 |
| SL | `stop_loss_pips ≥ 5` when FIXED | On UPDATE_PARAMS | REJECT_SET | E1013 |
| TP | `take_profit_pips ≥ 5` when FIXED | On UPDATE_PARAMS | REJECT_SET | E1014 |
| ATR | Period in [5,200]; TF in allowed set | On UPDATE_PARAMS | REJECT_SET | E1020 |
| Pending | `pending_order_timeout_min ∈ [1,1440]` | On UPDATE_PARAMS | CLAMP_TO_RANGE | W2003 |
| Retries | `order_retry_attempts ∈ [0,10]` | On UPDATE_PARAMS | CLAMP_TO_RANGE | W2004 |
| Chain | Generation must be `≤ R2` | Pre‑Reentry | REJECT_TRADE | E1030 |
| Time/News | Honor `eco_cutoff_minutes_*` windows | Pre‑OrderSend | REJECT_TRADE | E1040 |
| Health | If validation fails → keep last‑known‑good params | On UPDATE_PARAMS | PRESERVE_STATE | I0001 |

**Logging:** Every failure must append a row in `trade_responses.csv` with `status=ERROR` and include the failed field and value in `detail_json`.

---

## 5) Invariants, Determinism & Test Cues

- **Risk is derived**: `lots` are *never* direct inputs; EA computes from `effective_risk` and instrument contract size.  
- **CSV is the contract**: if a field isn’t here, the EA doesn’t depend on it.  
- **Deterministic chain**: Generations restricted to `O → R1 → R2`.  
- **ECO duration restriction**: Only ECO signals accept `duration` segment.  
- **Strict IDs**: `parameter_set_id` and `combination_id` must match regex/grammar.

**Unit tests (suggested):**
1. Schema: reject `global_risk_percent=5.0` (E1001).  
2. SL/TP relation: `SL=50, TP=30` → REJECT_SET (E1012).  
3. ATR: `sl_atr_period=2` → REJECT_SET (E1020).  
4. Pending clamp: `pending_order_timeout_min=0` → CLAMP to 1 (W2003).  
5. Chain: Attempt `R3:*` → REJECT_TRADE (E1030).

---

## 6) UI Control Hints (for generator)

| Param | Control | Validation UX |
|---|---|---|
| global_risk_percent | numeric input (step 0.01) | live range badge, warn > 2.00 |
| stop_loss_method | dropdown | conditionally reveal FIXED/ATR/PERCENT fields |
| entry_order_type | segmented buttons | show/hide straddle group |
| trailing_stop_method | dropdown | disable group when DISABLED |
| parameter_set_id | readonly text | auto-generated slug from template |

---

## 7) Directory & File Layout

```
Common/Files/reentry/
  bridge/
    trading_signals.csv        # Python → EA (append‑only)
    trade_responses.csv        # EA → Python (append‑only)
  logs/
    parameter_log.csv          # EA parameter echoes
  config/
    matrix_map.csv             # combination_id → parameter_set_id mapping
    parameters.schema.json     # JSON Schema (generated)
```

---

## 8) Examples

### 8.1 UPDATE_PARAMS (embedded in trading_signals.csv → json_payload)
```json
{
  "parameter_set_id": "PS-eco-r1-atr2",
  "global_risk_percent": 1.20,
  "risk_multiplier": 1.00,
  "max_risk_cap_percent": 3.50,
  "stop_loss_method": "ATR",
  "sl_atr_multiple": 2.0,
  "sl_atr_period": 14,
  "sl_atr_timeframe": "H1",
  "take_profit_method": "RR",
  "rr_target": 2.0,
  "entry_order_type": "STRADDLE",
  "straddle_buy_distance_pips": 15,
  "straddle_sell_distance_pips": 15,
  "straddle_auto_cancel_opposite": true,
  "pending_order_timeout_min": 120
}
```

### 8.2 TRADE_RESPONSE (EA → Python row)
```json
{
  "version":"3.0",
  "timestamp_utc":"2025-08-20T13:05:11Z",
  "symbol":"EURUSD",
  "combination_id":"R1:ECO_HIGH:QUICK:SHORT:LOSS",
  "action":"ACK_UPDATE",
  "status":"OK",
  "ea_code":"",
  "detail_json":"{\"message\":\"Params accepted\"}"
}
```

---

## 9) Change Control

- **v3.0 (2025‑08‑20)**: CSV‑only transport; ECO‑only duration; generation cap at R2; unified risk‑first sizing; formal CSV schemas; validation codes introduced.

**Breaking change handling:** Bump `version` field in all CSVs; EA rejects rows with incompatible versions.

---

## 10) Implementation Notes (EA)

- Read `trading_signals.csv` tail‑append with file locking; ignore partial lines.  
- On `UPDATE_PARAMS`: validate against schema mirror; persist last‑known‑good only after pass.  
- Derive lot size from `effective_risk` and symbol contract size; round to broker min step.  
- On `STRADDLE`: place symmetric pending orders; if one legs in, cancel the other if `straddle_auto_cancel_opposite=true`.  
- Respect `pending_order_timeout_min`: auto‑delete stale pendings.

---

## 11) Implementation Notes (Python)

- Generate `parameters.schema.json` from YAML (§1.1) at build time.  
- Validate parameter JSON before emitting to CSV; compute and include `json_payload_sha256`.  
- Maintain `matrix_map.csv`; resolve `combination_id → parameter_set_id` deterministically.  
- Emit `HEARTBEAT` rows every 30s for liveness; EA echoes with `HEARTBEAT` in `trade_responses.csv`.

---

## 12) Glossary

- **Effective risk**: The *final* risk used to compute position size after applying multiplier and cap.  
- **Combination ID**: Deterministic key representing the current chain generation, signal class, optional duration (ECO only), proximity bucket, and latest outcome.

