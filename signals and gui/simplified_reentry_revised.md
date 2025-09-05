# Simplified Reentry Trading System - Complete Implementation Plan

## System Overview

A deterministic trade reentry system with maximum 2 reentries per original signal, using future event proximity-based decision making and comprehensive governance controls.

## Core Architecture

### Signal Classification
**Original Trades:**
- **Volatility Events:** ECO_HIGH, ECO_MED, ANTICIPATION_1HR/4HR/8HR/12HR, EQUITY_OPEN_ASIA/EUROPE/USA
- **Price Derived:** ALL_INDICATORS (placeholder for specific technical indicators)

**Reentry Trades:**
- Based on: Original signal type + Outcome bucket (1-6) + Duration category + Future event proximity

### Decision Matrix Dimensions

#### Original Trade Variables
1. **Signal Type** (10 types)
2. **Proximity to Future Event** (6 buckets: Immediate/Short/Medium/Long/Extended/Tomorrow/None)

#### Reentry Variables  
1. **Original Signal Type** (10 types)
2. **Outcome Bucket** (1-6: Full SL → Beyond TP)
3. **Duration Category** (5 types: Flash/Quick/Medium/Long/Extended)
4. **Proximity to Future Event** (6 buckets)

### Time Categories
- **Flash:** 0-5 minutes
- **Quick:** 6-15 minutes  
- **Medium:** 16-45 minutes
- **Long:** 46-90 minutes
- **Extended:** >90 minutes

### Proximity Buckets
- **Immediate:** 0-5 minutes
- **Short:** 5-60 minutes
- **Medium:** 61-240 minutes  
- **Long:** 241-480 minutes
- **Extended:** 481-720 minutes
- **Tomorrow:** 721-1440 minutes
- **None:** No events in 24hr window

## Governance Controls & Risk Management

### Core Controls
| Control | Purpose | Default | Range |
|---------|---------|---------|-------|
| AllowReentry | Global enable/disable | 1 | 0 or 1 |
| MinDelaySeconds | Minimum reentry delay | 0 | ≥0 |
| MaxGenerations | Max reentries allowed | 2 | 0-2 |
| DailyLossLimit | Daily loss threshold | - | Currency amount |
| MinConfidence | Required confidence level | 0.7 | 0.0-1.0 |
| BlackoutAfterLosses | Pause after N losses | 3 | ≥1 |
| BlackoutMinutes | Blackout duration | 60 | ≥0 |
| MaxPositionSize | Lot size cap | - | >0 |
| MaxSpreadPoints | Spread limit | 30 | Points |

### Emergency Stops
- Daily drawdown limits
- Consecutive loss streaks
- Correlation emergency stop
- Maximum trades per hour/minute

## Economic Calendar Integration

### Data Source
- **Primary:** ForexFactory CSV (ff_calendar_thisweek.csv)
- **Format:** Title, Country, Date, Time, Impact, Forecast, Previous, URL
- **Update:** Automated weekly download

### Processing Pipeline
1. Download latest ForexFactory data
2. Filter High/Medium impact events
3. Exclude CHF events
4. Create anticipation signals (1HR/4HR/8HR/12HR before)
5. Add equity market opens (Asia 21:00, Europe 02:00, USA 08:30 CST)
6. Calculate proximity to future events only
7. Export to MT4-ready format

### Event Types Generated
- **Economic Events:** Direct high/medium impact trades
- **Anticipation Events:** "2H Before NFP Anticipation - USD - High"
- **Equity Opens:** "Tokyo Market Open (USD/JPY)" 

## Database Schema

### Per-Symbol Tables
```sql
-- Core trade tracking
trades_SYMBOL (
    trade_id, magic_number, open_time, close_time,
    signal_type, outcome_bucket, duration_category,
    proximity_future,
    is_reentry, reentry_generation, chain_id
)

-- Reentry chain management  
reentry_chains_SYMBOL (
    chain_id, original_trade_id, chain_length,
    total_pnl, status, combination_history
)

-- Execution tracking
reentry_executions_SYMBOL (
    execution_id, chain_id, combination_id,
    parameter_set_id, size_multiplier, 
    confidence_used, delay_used, pnl
)

-- Performance analytics
reentry_performance_SYMBOL (
    combination_id, action_no, parameter_set_id,
    total_executions, successful_executions,
    total_pnl, success_rate, last_execution
)
```

### Magic Number System
- **Base Magic:** User-defined starting number
- **Original Trades:** Base + 0
- **First Reentry:** Base + 10000  
- **Second Reentry:** Base + 20000

## Parameter Sets & Configuration

### CSV-Driven Configuration
Each symbol gets configuration files:
- `EURUSD_reentry.csv` - Parameter sets 1-6 for outcomes
- `EURUSD_governance.csv` - Risk controls and limits

### Parameter Set Structure
```csv
ActionNo,ParameterSetID,SizeMultiplier,StopLossPips,TakeProfitPips,
DelaySeconds,ConfidenceAdjustment,MaxSpreadPips,EntryMethod
1,101,0.0,0,0,0,1.0,30,NONE
2,102,1.2,25,50,30,1.1,25,MARKET
3,103,1.5,20,40,60,1.2,20,PENDING
...
```

### Profile Management
- **Personas:** Conservative, Moderate, Aggressive
- **Deployment:** PowerShell scripts rotate profiles daily
- **Automation:** Windows Task Scheduler handles profile switching

## Combination Mapping System

### Combination IDs
**Format:** `SYMBOL:SIGNAL:DURATION:O{outcome}:F{future}:G{generation}`
**Example:** `EURUSD:ECO_HIGH:QUICK:O4:FSHORT:G1`

### Decision Logic
1. Trade closes → Calculate combination ID
2. Lookup parameter set for combination  
3. Apply governance controls
4. Execute reentry or end chain
5. Track performance and update analytics

### Auto-Rules
- **No Trade:** Immediate proximity to future volatility blocks all trades
- **Chain Limit:** Maximum 2 reentries, then force end
- **Blackout:** After consecutive losses, pause all reentries

## Performance Analytics & Optimization

### KPI Tracking
- Per-combination success rates
- Chain-level profitability
- Parameter set effectiveness
- Risk-adjusted returns

### Automated Reports
- **Daily:** Profile rotation logs
- **Weekly:** KPI exports and performance summaries  
- **Monthly:** Optimization recommendations

### Optimization Process
1. Collect minimum 100 executions per combination
2. Analyze success rates and risk metrics
3. User manually adjusts parameter sets
4. Deploy updated configurations
5. Monitor performance changes

## Implementation Workflow

### Phase 1: Core System
1. Database schema setup per symbol
2. Economic calendar integration
3. Basic combination mapping
4. Parameter set configuration

### Phase 2: Governance & Safety
1. Risk control implementation
2. Emergency stop mechanisms
3. Chain tracking and limits
4. Performance monitoring

### Phase 3: Automation & Analytics
1. Profile deployment automation
2. KPI export and reporting
3. Optimization workflows
4. Production monitoring

## Key Simplifications from Original

1. **Fixed Reentry Limit:** Maximum 2 reentries (vs unlimited generations)
2. **Future-Only Context:** Uses only future event proximity for decision making (past events removed)
3. **Automated Calendar:** ForexFactory integration replaces manual event management
4. **Deterministic Rules:** Pre-mapped combinations eliminate real-time decision making
5. **Built-in Safety:** Governance controls prevent runaway trading

## Expected Combination Counts

- **Original Trades:** 10 signals × 6 future = 60 combinations per symbol
- **First Reentries:** 10 signals × 6 outcomes × 5 durations × 6 future = 1,800 combinations
- **Second Reentries:** Same as first = 1,800 combinations
- **Total:** 3,660 combinations per symbol

This creates a manageable decision matrix that handles realistic trading scenarios while maintaining simplicity and safety with 83% fewer combinations than the original design.