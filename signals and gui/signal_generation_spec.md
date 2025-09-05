# Claude Trading System - Signal Generation Technical Reference

## Overview

This document serves as the complete technical specification for the Claude-based Signal Generation Service within the multi-component trading system. It defines the exact logic, constraints, data structures, and behavioral patterns required to generate trading signals with consistent fidelity across different AI implementations.

## 1. Core Signal Generation Logic

### 1.1 Signal Trigger Conditions

Signals are generated based on the following conditions:

**Primary Triggers:**
- Time-based intervals (configurable via `decision_frequency` in YAML config)
- Market volatility thresholds (symbol-specific)
- Confluence of multiple technical indicators
- Risk-reward ratio meets minimum threshold (1:2 default)

**Signal Suppression Conditions:**
- Recent signal for same symbol within cooldown period (default: 300 seconds)
- Maximum daily signal limit reached per symbol (default: 20)
- Market session filters (avoid low-liquidity periods)
- System health check failures

### 1.2 Signal Validation Pipeline

Before generation, each potential signal must pass:
1. **Symbol Validation**: Must be in configured trading pairs list
2. **Market Hours Check**: Symbol must be in active trading session
3. **Cooldown Verification**: No recent signals for same symbol
4. **Risk Management**: Portfolio exposure limits not exceeded
5. **Quality Gate**: Minimum confidence threshold met

## 2. Confidence Determination

### 2.1 Base Confidence Calculation

```python
def calculate_base_confidence(symbol, market_data):
    base_confidence = 0.5  # Starting point
    
    # Technical indicator alignment (0.0 to 0.3)
    technical_score = analyze_technical_confluence(market_data)
    
    # Volatility adjustment (-0.1 to +0.1)
    volatility_factor = min(0.1, max(-0.1, (market_data.atr - market_data.avg_atr) / market_data.avg_atr))
    
    # Symbol-specific bonus
    symbol_bonus = SYMBOL_CONFIDENCE_BONUS.get(symbol, 0.0)
    
    confidence = base_confidence + technical_score + volatility_factor + symbol_bonus
    return min(1.0, max(0.0, confidence))
```

### 2.2 Symbol-Specific Confidence Bonuses

```python
SYMBOL_CONFIDENCE_BONUS = {
    'EURUSD': 0.05,  # Major pair, high liquidity
    'GBPUSD': 0.03,  # Major pair, moderate volatility
    'AUDUSD': 0.02,  # Commodity currency factor
    'USDCAD': 0.02,  # Oil correlation bonus
    'USDJPY': 0.04,  # Central bank intervention awareness
    'AUDNZD': 0.01,  # Cross pair, lower liquidity
}
```

### 2.3 Confidence Modifiers

**Trend Strength Bonus (+0.0 to +0.15):**
- Strong trend: +0.15
- Moderate trend: +0.08
- Weak/sideways: +0.00

**Market Session Bonus:**
- London/NY overlap: +0.05
- Single major session: +0.02
- Asian session only: -0.05

**Random Variation Range:**
- Apply ±0.03 random adjustment to final confidence
- Prevents mechanical signal patterns
- Uses seeded random for reproducibility during testing

## 3. Direction Selection Logic

### 3.1 Primary Direction Determination

```python
def determine_direction(symbol, market_data, recent_signals):
    # Technical analysis score (-1.0 to +1.0)
    technical_bias = calculate_technical_bias(market_data)
    
    # Recent performance adjustment
    performance_modifier = analyze_recent_performance(symbol, recent_signals)
    
    # Risk management override
    portfolio_bias = check_portfolio_exposure(symbol)
    
    final_score = technical_bias + performance_modifier + portfolio_bias
    
    if final_score > 0.1:
        return "BUY"
    elif final_score < -0.1:
        return "SELL"
    else:
        # Neutral zone - use probability-based selection
        return "BUY" if random.random() > 0.5 else "SELL"
```

### 3.2 Behavioral Logic Patterns

**Anti-Martingale Protection:**
- After 2 consecutive losses in same direction, reduce probability by 30%
- After 3 consecutive losses, temporarily avoid that direction (60-minute cooldown)

**Portfolio Balance:**
- If >60% of open positions are BUY, increase SELL probability by 20%
- If >60% of open positions are SELL, increase BUY probability by 20%

**Market Regime Adaptation:**
- Trending markets: Follow momentum (80% probability)
- Range-bound markets: Fade extremes (70% probability)

## 4. Strategy ID Generation

### 4.1 Strategy ID Format

**Format:** 5-digit numeric string (e.g., "12345")

**Generation Logic:**
```python
def generate_strategy_id(symbol, direction, timestamp):
    # Components:
    # Digits 1-2: Symbol hash (01-99)
    # Digit 3: Direction (1=BUY, 2=SELL)  
    # Digits 4-5: Time component (00-99)
    
    symbol_hash = hash(symbol) % 99 + 1  # 01-99
    direction_code = 1 if direction == "BUY" else 2
    time_component = (timestamp.minute + timestamp.second) % 100  # 00-99
    
    return f"{symbol_hash:02d}{direction_code}{time_component:02d}"
```

### 4.2 Uniqueness Guarantee

- Strategy IDs are unique within a 24-hour rolling window
- Collision detection with retry mechanism (max 3 attempts)
- Fallback to UUID-based numeric conversion if collisions persist

## 5. Signal Format Specification

### 5.1 Required Fields

```python
@dataclass
class TradingSignal:
    id: str              # UUIDv4 format
    symbol: str          # 6 uppercase characters (e.g., "EURUSD")
    direction: str       # "BUY" or "SELL" only
    confidence: float    # Range [0.0, 1.0]
    timestamp: str       # ISO8601 format with timezone
    strategy_id: str     # 5-digit numeric string
    metadata: str        # JSON string with additional data
```

### 5.2 Validation Rules

**Field Validation:**
- `id`: Must be valid UUIDv4 format
- `symbol`: Exactly 6 uppercase letters, must be in configured pairs list
- `direction`: Must be exactly "BUY" or "SELL" (case-sensitive)
- `confidence`: Float between 0.0 and 1.0 (inclusive)
- `timestamp`: ISO8601 with timezone (e.g., "2024-12-09T14:30:45.123Z")
- `strategy_id`: Exactly 5 digits, numeric string format
- `metadata`: Valid JSON string or empty string

**Business Rule Validation:**
- Confidence must exceed configured threshold (default: 0.6)
- Symbol must be currently tradeable
- No duplicate signals within cooldown period

### 5.3 Metadata Structure

```json
{
    "source": "claude_signal_service",
    "generation_time": "2024-12-09T14:30:45.123Z",
    "base_confidence": 0.67,
    "symbol_bonus": 0.05,
    "technical_score": 0.23,
    "volatility_factor": 0.02,
    "market_session": "london_ny_overlap",
    "recent_performance": "neutral"
}
```

## 6. Configuration Sensitivity

### 6.1 Key Configuration Parameters

```yaml
signal_generation:
  confidence_threshold: 0.6        # Minimum confidence to generate signal
  decision_frequency: 300          # Seconds between signal evaluations
  max_daily_signals: 20           # Per symbol limit
  cooldown_period: 300            # Seconds between signals for same symbol
  symbols: ["EURUSD", "GBPUSD"]   # Trading pairs to monitor
  
risk_management:
  max_portfolio_exposure: 0.6     # Maximum percentage in one direction
  position_sizing: "fixed"        # fixed, percentage, or dynamic
  
market_hours:
  respect_sessions: true          # Honor trading session filters
  avoid_news_events: true         # Skip signals near high-impact news
```

### 6.2 Fallback Behavior

**Missing Configuration Values:**
- `confidence_threshold`: Default to 0.6
- `decision_frequency`: Default to 300 seconds
- `max_daily_signals`: Default to 20
- `symbols`: Default to ["EURUSD", "GBPUSD", "USDJPY"]

**Invalid Configuration Values:**
- Log warning and use nearest valid value
- confidence_threshold clamped to [0.5, 0.95]
- decision_frequency clamped to [60, 3600] seconds

## 7. File Output Format

### 7.1 CSV Structure

**File Naming Convention:**
```
MT4/Files/signals/{SYMBOL}_signals.csv
```

**CSV Column Order (Exact):**
```csv
id,symbol,direction,confidence,timestamp,strategy_id,metadata
```

**Example CSV Content:**
```csv
id,symbol,direction,confidence,timestamp,strategy_id,metadata
f47ac10b-58cc-4372-a567-0e02b2c3d479,GBPUSD,BUY,0.72,2024-12-09T14:30:45.123Z,34127,"{""source"":""claude_signal_service""}"
a1b2c3d4-e5f6-7890-abcd-ef1234567890,EURUSD,SELL,0.68,2024-12-09T14:35:12.456Z,15289,"{""source"":""claude_signal_service""}"
```

### 7.2 File Management

**Write Operations:**
- Append new signals to existing file
- Create file with headers if doesn't exist
- Atomic write operations to prevent corruption
- Automatic file rotation at 10MB or 10,000 rows

**File Permissions:**
- Read/write access for service account
- Read-only access for MT4 terminal

## 8. Health & Quality Control

### 8.1 Health Check Criteria

**Service Health Indicators:**
- Signal generation rate within expected range
- Error rate below 5% threshold
- File write operations successful
- Configuration file accessible and valid
- No memory leaks or resource exhaustion

**Health Check Response:**
```python
def health_check(self):
    stats = self.get_statistics()
    
    checks = {
        "signals_generated": stats.signal_count > 0,
        "error_rate": stats.error_rate < 0.05,
        "last_signal_recent": (datetime.now() - stats.last_signal_time).seconds < 1800,
        "file_accessible": self.can_write_signals(),
        "config_valid": self.validate_config()
    }
    
    return {
        "healthy": all(checks.values()),
        "checks": checks,
        "statistics": stats
    }
```

### 8.2 Error Classification

**Generation Errors:**
- Invalid symbol configuration
- Confidence calculation failure
- File write permission errors
- Market data unavailable

**Quality Errors:**
- Signals below confidence threshold
- Duplicate signal detection
- Configuration validation failures

### 8.3 Statistics Tracking

**Tracked Metrics:**
- Total signals generated (lifetime)
- Signals per symbol breakdown
- Average confidence levels
- Direction distribution (BUY/SELL ratio)
- Error counts by type
- Last successful signal timestamp
- File operation success rate

## 9. Complete Working Example

### 9.1 Signal Generation Scenario

**Input Conditions:**
- Symbol: GBPUSD
- Current time: 2024-12-09T14:30:45.123Z
- Market: London/NY overlap session
- Recent volatility: Slightly above average
- No recent signals for GBPUSD

### 9.2 Step-by-Step Generation

```python
# 1. Calculate base confidence
base_confidence = 0.5
technical_score = 0.18  # Moderate bullish alignment
volatility_factor = 0.04  # Above average volatility bonus
symbol_bonus = 0.03  # GBPUSD bonus
random_variation = 0.02  # Random adjustment

final_confidence = 0.5 + 0.18 + 0.04 + 0.03 + 0.02 = 0.77

# 2. Determine direction  
technical_bias = 0.15  # Bullish signals
performance_modifier = 0.0  # Neutral recent performance
portfolio_bias = -0.05  # Slight overweight in BUY positions

direction_score = 0.15 + 0.0 + (-0.05) = 0.10
direction = "BUY"  # Score > 0.1

# 3. Generate strategy ID
symbol_hash = hash("GBPUSD") % 99 + 1 = 34
direction_code = 1  # BUY
time_component = (30 + 45) % 100 = 75
strategy_id = "34175"

# 4. Create signal object
signal = {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "symbol": "GBPUSD", 
    "direction": "BUY",
    "confidence": 0.77,
    "timestamp": "2024-12-09T14:30:45.123Z",
    "strategy_id": "34175",
    "metadata": json.dumps({
        "source": "claude_signal_service",
        "generation_time": "2024-12-09T14:30:45.123Z",
        "base_confidence": 0.5,
        "technical_score": 0.18,
        "symbol_bonus": 0.03,
        "volatility_factor": 0.04,
        "market_session": "london_ny_overlap"
    })
}
```

### 9.3 CSV Output

**File:** `MT4/Files/signals/GBPUSD_signals.csv`
**New Row:**
```csv
f47ac10b-58cc-4372-a567-0e02b2c3d479,GBPUSD,BUY,0.77,2024-12-09T14:30:45.123Z,34175,"{""source"":""claude_signal_service"",""generation_time"":""2024-12-09T14:30:45.123Z"",""base_confidence"":0.5,""technical_score"":0.18,""symbol_bonus"":0.03,""volatility_factor"":0.04,""market_session"":""london_ny_overlap""}"
```

### 9.4 Validation Checklist

- ✅ UUID format valid
- ✅ Symbol is 6 uppercase characters
- ✅ Direction is "BUY" or "SELL"
- ✅ Confidence in range [0.0, 1.0]
- ✅ Confidence above threshold (0.77 > 0.6)
- ✅ Timestamp in ISO8601 format
- ✅ Strategy ID is 5-digit numeric string
- ✅ Metadata is valid JSON string
- ✅ No recent signal for GBPUSD (cooldown check)
- ✅ Daily signal limit not exceeded

## 10. Implementation Notes

### 10.1 BaseService Integration

The SignalService must inherit from BaseService and implement exactly three methods:

```python
class SignalService(BaseService):
    def start(self):
        # Initialize signal generation loop
        pass
        
    def stop(self):
        # Clean shutdown and resource cleanup
        pass
        
    def health_check(self):
        # Return health status dict
        pass
```

### 10.2 Thread Safety

- All signal generation operations must be thread-safe
- Use file locking for CSV write operations
- Atomic updates for internal statistics

### 10.3 Error Handling

- All exceptions must be caught and logged
- Service should continue operating after individual signal failures
- Graceful degradation when market data is unavailable

---

**Document Version:** 1.0  
**Last Updated:** 2024-12-09  
**Compatible With:** Claude Trading System v2.0+