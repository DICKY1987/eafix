# Economic Calendar to Signal System - Detailed Breakdown

## 🔍 STEP 1: DATA ACQUISITION LAYER (Import & Validate)

### Step 1.1: File Detection Logic
```
SEARCH_LOCATION: Downloads folder
SEARCH_PATTERNS: ["*calendar*.csv", "*economic*.csv", "ff_*.csv"]
TIMING: Every Sunday 12:00 PM CST + hourly retries

IF (Current_Day = Sunday AND Current_Time >= 12:00 PM CST) THEN
    Execute_Import_Process()
ELSE
    Schedule_Next_Import_Attempt()
```

### Step 1.2: File Validation Rules
```
REQUIRED_COLUMNS: [Title, Country, Date, Time, Impact]
MINIMUM_ROWS: 10
DATE_FORMAT: MM-DD-YYYY
TIME_FORMAT: H:MMam/pm
VALID_IMPACTS: [High, Medium, Low, Holiday]

VALIDATION_CHECKS:
├── File_Size > 1KB
├── Modified_Date = Today
├── Contains_Required_Columns = TRUE
├── Row_Count >= MINIMUM_ROWS
└── Date_Range_Covers_Current_Week = TRUE
```

**❓ QUESTIONS & GAPS:**
1. **What happens if multiple calendar files exist?** (Priority rules?)
2. **Should we validate against specific event types?** (NFP, FOMC, etc.)
3. **How do we handle duplicate events across files?**

---

## 🔄 STEP 2: DATA TRANSFORMATION PIPELINE

### Step 2.1: Raw Data Parsing
```
FOR each row IN raw_csv:
    parsed_event = {
        title: TRIM(row.Title),
        country: NORMALIZE_CURRENCY(row.Country),
        date: PARSE_DATE(row.Date, "MM-DD-YYYY"),
        time: PARSE_TIME(row.Time, "H:MMam/pm"),
        impact: NORMALIZE_IMPACT(row.Impact),
        forecast: row.Forecast,
        previous: row.Previous
    }
    
    IF (VALIDATE_EVENT(parsed_event)) THEN
        parsed_events.ADD(parsed_event)
```

### Step 2.2: Time Zone Conversion to CST
```
FUNCTION Convert_To_CST(date, time):
    // Calendar times appear to already be in CST based on sample
    base_datetime = COMBINE(date, time)
    
    // Check for Daylight Saving Time
    IF (IS_DST_PERIOD(date)) THEN
        cst_datetime = base_datetime  // Already CST
    ELSE
        cst_datetime = base_datetime  // Already CST
    END IF
    
    RETURN cst_datetime

FUNCTION IS_DST_PERIOD(date):
    // DST: Second Sunday in March to First Sunday in November
    dst_start = SECOND_SUNDAY_OF_MARCH(date.year)
    dst_end = FIRST_SUNDAY_OF_NOVEMBER(date.year)
    
    RETURN (date >= dst_start AND date < dst_end)
```

### Step 2.3: Impact Filtering & Classification
```
IMPACT_FILTER_RULES:
├── "High" → KEEP (Assign EMO-E code)
├── "Medium" → KEEP (Assign EMO-A code) 
├── "Low" → DISCARD
└── "Holiday" → DISCARD

FUNCTION Normalize_Impact(raw_impact):
    SWITCH UPPER(raw_impact):
        CASE "HIGH": RETURN "EMO-E"
        CASE "MEDIUM": RETURN "EMO-A"
        DEFAULT: RETURN "DISCARD"
```

**❓ QUESTIONS & GAPS:**
1. **Should "Holiday" events be treated differently?** (Market closure consideration?)
2. **How do we handle time conflicts when converting to CST?**
3. **What's the rule for events without specific times?** (All day events?)

---

## ⏳ STEP 3: EVENT ENHANCEMENT ENGINE

### Step 3.1: Equity Market Events Injection
```
EQUITY_MARKET_EVENTS = [
    {name: "Tokyo Open", time: "21:00 CST", pairs: ["USD/JPY", "AUD/JPY"], code: "EQT-OPEN"},
    {name: "London Open", time: "02:00 CST", pairs: ["EUR/USD", "GBP/USD"], code: "EQT-OPEN"},
    {name: "New York Open", time: "08:30 CST", pairs: ["USD/***"], code: "EQT-OPEN"}
]

FOR each weekday IN current_week:
    FOR each market IN EQUITY_MARKET_EVENTS:
        IF (market.active_days.CONTAINS(weekday)) THEN
            equity_event = CREATE_EQUITY_EVENT(market, weekday)
            enhanced_events.ADD(equity_event)
```

### Step 3.2: Anticipation Events Generation
```
USER_CONFIG = {
    anticipation_hours: [1, 2, 4],    // User configurable
    max_anticipation_count: 3,        // User configurable
    enabled: TRUE                     // Toggle on/off
}

FOR each original_event IN filtered_events:
    IF (original_event.impact IN ["EMO-E", "EMO-A"]) THEN
        FOR each hour_offset IN USER_CONFIG.anticipation_hours:
            anticipation_event = {
                title: "#{hour_offset}H Before {original_event.title} Anticipation",
                country: original_event.country,
                date: original_event.date,
                time: original_event.time - (hour_offset * 60_minutes),
                impact: original_event.impact,  // Inherit impact level
                event_type: "ANTICIPATION",
                original_event_id: original_event.id,
                hours_before: hour_offset
            }
            enhanced_events.ADD(anticipation_event)
```

**❓ QUESTIONS & GAPS:**
1. **Should anticipation events have different impact levels?** (Lower than original?)
2. **What happens if anticipation time goes to previous day?**
3. **How do we prevent anticipation overlap with other events?**

---

## 📊 STEP 4: PERFORMANCE OSCILLATOR LOGIC

### Step 4.1: Data Collection for Oscillator
```
FUNCTION Collect_Performance_Data():
    current_time = GET_CURRENT_TIME()
    four_hours_ago = current_time - (4 * 60 * 60 * 1000)  // 4 hours in milliseconds
    
    recent_trades = GET_TRADES_IN_TIMEFRAME(four_hours_ago, current_time)
    account_data = GET_ACCOUNT_DATA()
    
    performance_data = {
        consecutive_losses: CALCULATE_CONSECUTIVE_LOSSES(recent_trades),
        equity_drawdown: CALCULATE_EQUITY_DRAWDOWN(account_data, four_hours_ago),
        total_trades: recent_trades.length,
        win_rate: CALCULATE_WIN_RATE(recent_trades)
    }
    
    RETURN performance_data
```

### Step 4.2: Consecutive Losses Calculation
```
FUNCTION CALCULATE_CONSECUTIVE_LOSSES(trades):
    consecutive_losses = 0
    
    // Sort trades by close time (most recent first)
    sorted_trades = SORT_BY_CLOSE_TIME_DESC(trades)
    
    FOR each trade IN sorted_trades:
        IF (trade.profit < 0) THEN
            consecutive_losses++
        ELSE
            BREAK  // Stop at first winning trade
        END IF
    END FOR
    
    RETURN consecutive_losses
```

### Step 4.3: Equity Drawdown Calculation
```
FUNCTION CALCULATE_EQUITY_DRAWDOWN(account_data, start_time):
    equity_history = GET_EQUITY_HISTORY(start_time, current_time)
    
    IF (equity_history.length < 2) THEN
        RETURN 0  // Not enough data
    END IF
    
    peak_equity = MAX(equity_history)
    current_equity = LAST(equity_history)
    
    drawdown_percentage = ((peak_equity - current_equity) / peak_equity) * 100
    
    RETURN MAX(drawdown_percentage, 0)  // Never negative
```

### Step 4.4: Oscillator Value Calculation
```
FUNCTION CALCULATE_OSCILLATOR_VALUE(performance_data):
    // Weighted scoring based on recent performance
    
    // Consecutive losses penalty (0-50 points)
    loss_penalty = MIN(performance_data.consecutive_losses * 10, 50)
    
    // Equity drawdown penalty (0-40 points) 
    drawdown_penalty = MIN(performance_data.equity_drawdown * 2, 40)
    
    // Base score starts at 100
    base_score = 100
    
    // Apply penalties
    oscillator_value = base_score - loss_penalty - drawdown_penalty
    
    // Ensure within bounds
    oscillator_value = CLAMP(oscillator_value, 0, 100)
    
    RETURN oscillator_value

FUNCTION CLAMP(value, min_val, max_val):
    RETURN MAX(min_val, MIN(value, max_val))
```

**❓ QUESTIONS & GAPS:**
1. **What if there are no trades in the last 4 hours?** (Default oscillator value?)
2. **Should we weight recent losses more heavily than older ones?**
3. **How often should the oscillator be recalculated?** (Real-time vs. per-event?)

---

## 🎯 STEP 5: STRATEGY EXECUTION FRAMEWORK

### Step 5.1: Event Trigger Monitoring
```
FUNCTION Monitor_Event_Triggers():
    WHILE (system_active) DO
        current_time = GET_CURRENT_TIME_CST()
        
        FOR each event IN active_calendar:
            // Calculate trigger time with offset
            trigger_time = event.time - event.offset_minutes
            
            // Check if within trigger window (±30 seconds)
            time_difference = ABS(current_time - trigger_time)
            
            IF (time_difference <= 30_seconds AND event.triggered = FALSE) THEN
                EXECUTE_STRATEGY_TRIGGER(event)
                event.triggered = TRUE
            END IF
        END FOR
        
        SLEEP(15_seconds)  // Check every 15 seconds
    END WHILE
```

### Step 5.2: Offset Configuration Rules
```
OFFSET_RULES = {
    "EMO-E": -3_minutes,      // High impact events
    "EMO-A": -2_minutes,      // Medium impact events  
    "EQT-OPEN": -5_minutes,   // Equity market opens
    "ANTICIPATION": -1_minute // Anticipation events
}

FUNCTION GET_EVENT_OFFSET(event):
    base_offset = OFFSET_RULES[event.impact]
    user_adjustment = GET_USER_OFFSET_SETTING()  // Global user adjustment
    
    final_offset = base_offset + user_adjustment
    
    RETURN final_offset
```

### Step 5.3: Parameter Set Selection
```
PARAMETER_SETS = {
    "CONSERVATIVE": {  // Oscillator 0-25
        lot_size: 0.01,
        stop_loss: 30,
        take_profit: 60,
        buy_distance: 5,
        sell_distance: 5,
        max_spread: 2
    },
    "MODERATE": {      // Oscillator 26-50
        lot_size: 0.02,
        stop_loss: 20,
        take_profit: 40,
        buy_distance: 10,
        sell_distance: 10,
        max_spread: 3
    },
    "AGGRESSIVE": {    // Oscillator 51-75
        lot_size: 0.05,
        stop_loss: 15,
        take_profit: 30,
        buy_distance: 15,
        sell_distance: 15,
        max_spread: 4
    },
    "MAXIMUM": {       // Oscillator 76-100
        lot_size: 0.10,
        stop_loss: 10,
        take_profit: 20,
        buy_distance: 20,
        sell_distance: 20,
        max_spread: 5
    }
}

FUNCTION SELECT_PARAMETER_SET(oscillator_value):
    IF (oscillator_value <= 25) THEN RETURN "CONSERVATIVE"
    ELSIF (oscillator_value <= 50) THEN RETURN "MODERATE"  
    ELSIF (oscillator_value <= 75) THEN RETURN "AGGRESSIVE"
    ELSE RETURN "MAXIMUM"
```

**❓ QUESTIONS & GAPS:**
1. **Should different event types have different parameter sets?** (NFP vs. ECB vs. Equity Opens?)
2. **How do we handle overlapping trigger times?** (Priority system?)
3. **What if MT4 is offline during trigger time?** (Queue signals for later?)

---

## 🔄 STEP 6: SIGNAL ENTRY SHEET INTEGRATION

### Step 6.1: Currency Pair Determination
```
CURRENCY_MAPPING = {
    "USD": ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD", "NZD/USD", "USD/CAD"],
    "EUR": ["EUR/USD", "EUR/GBP", "EUR/JPY", "EUR/CHF", "EUR/AUD", "EUR/CAD"],
    "GBP": ["GBP/USD", "EUR/GBP", "GBP/JPY", "GBP/CHF", "GBP/AUD", "GBP/CAD"],
    "JPY": ["USD/JPY", "EUR/JPY", "GBP/JPY", "CHF/JPY", "AUD/JPY", "CAD/JPY"]
}

FUNCTION DETERMINE_CURRENCY_PAIRS(event):
    affected_pairs = []
    
    IF (event.country IN CURRENCY_MAPPING) THEN
        affected_pairs = CURRENCY_MAPPING[event.country]
    ELSE
        affected_pairs = ["EUR/USD"]  // Default fallback
    END IF
    
    RETURN affected_pairs
```

### Step 6.2: Signal Data Package Creation
```
FUNCTION CREATE_SIGNAL_PACKAGE(event, oscillator_value):
    parameter_set = SELECT_PARAMETER_SET(oscillator_value)
    currency_pairs = DETERMINE_CURRENCY_PAIRS(event)
    
    signal_package = {
        timestamp: GET_CURRENT_TIME(),
        event_name: event.title,
        event_type: event.impact,
        trigger_reason: event.event_type,
        oscillator_value: oscillator_value,
        parameter_set: parameter_set,
        currency_pairs: currency_pairs,
        strategy_id: GET_STRATEGY_ID(event),
        pset_id: GET_PSET_ID(parameter_set)
    }
    
    RETURN signal_package
```

---

## 🚨 CRITICAL QUESTIONS REQUIRING CLARIFICATION:

### 1. **Time Synchronization Issues:**
   - How do we handle daylight saving time transitions during the week?
   - What if the calendar source uses different time zones?

### 2. **Event Conflict Resolution:**
   - If two high-impact events occur within 5 minutes, which takes priority?
   - Should anticipation events be cancelled if too close to other events?

### 3. **Performance Data Requirements:**
   - Where does the 4-hour trade history come from? (MT4 EA, Excel log?)
   - How do we handle cold starts with no performance history?

### 4. **Signal Processing:**
   - Should each currency pair get a separate signal or batch processing?
   - How do we prevent duplicate signals for the same event?

### 5. **Error Handling:**
   - What happens if the calendar import fails on Sunday?
   - How do we handle missing or corrupted performance data?

### 6. **User Interface:**
   - Where do users configure anticipation hours and offset settings?
   - How do users monitor the oscillator value in real-time?

**These gaps need resolution before implementation to ensure the system works flawlessly!**