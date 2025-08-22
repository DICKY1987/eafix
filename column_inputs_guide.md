# Column Header Data Input Specifications

## Economic Calendar System

### Time
- **Input Source**: External economic data feed timestamps
- **Format**: Date format (YYYY-MM-DD HH:MM:SS)
- **Validation**: Must be valid datetime, future events allowed

### Currency
- **Input Source**: ISO currency codes from economic events
- **Format**: 3-character string (USD, EUR, GBP, etc.)
- **Validation**: Must match supported trading pairs

### Event
- **Input Source**: Economic event descriptions from data providers
- **Format**: String description of economic indicator
- **Examples**: "Non-Farm Payrolls", "CPI", "GDP"

### Impact
- **Input Source**: Event classification system
- **Format**: String enum (High, Medium, Low)
- **Determination**: Based on historical market volatility correlation

### Actual/Forecast/Previous
- **Input Source**: Economic data values from reporting agencies
- **Format**: Float values
- **Units**: Varies by indicator (%, points, millions, etc.)

## Reentry Matrix System

### Core Combinations Table

#### symbol
- **Input Source**: Trading pair from broker feed
- **Format**: String (EURUSD, GBPUSD, etc.)
- **Validation**: Must exist in supported pairs list

#### signal_type
- **Input Source**: Signal generation system classification
- **Format**: Enum string
- **Values**: ECO_HIGH, ECO_MED, EQUITY_OPEN_USA, ANTICIPATION_4HR, ALL_INDICATORS
- **Determination**: Based on signal trigger conditions

#### time_category
- **Input Source**: Trade duration classifier
- **Format**: Enum string
- **Values**: FLASH, QUICK, MEDIUM, LONG, EXTENDED
- **Mapping**:
  - FLASH: <5 minutes
  - QUICK: 5-30 minutes
  - MEDIUM: 30-120 minutes
  - LONG: 2-8 hours
  - EXTENDED: >8 hours

#### outcome
- **Input Source**: Trade result categorization algorithm
- **Format**: Integer (1-6)
- **Mapping**:
  - 1-2: Loss scenarios
  - 3: Breakeven
  - 4: Partial profit (25-75% of target)
  - 5: Target reached
  - 6: Exceeded target

#### context
- **Input Source**: Composite of future/past proximity analysis
- **Format**: String pattern "F[category]:[category]"
- **Components**:
  - Future proximity: FIMMEDIATE, FSHORT, FMEDIUM, FLONG, FNONE
  - Past proximity: PNONE, PYESTERDAY, PSHORT, PMEDIUM, PEXTENDED

#### generation
- **Input Source**: Reentry chain counter
- **Format**: Integer starting at 0
- **Increment**: +1 for each subsequent reentry in chain

#### combination_id
- **Input Source**: Concatenated key generator
- **Format**: Colon-separated string
- **Pattern**: {symbol}:{signal_type}:{time_category}:O{outcome}:{context}:G{generation}

### Response Parameters Table

#### decision
- **Input Source**: Decision engine output
- **Format**: Enum string
- **Values**: REENTRY, END_TRADING
- **Logic**: Based on outcome, performance history, risk parameters

#### size_multiplier
- **Input Source**: Position sizing algorithm
- **Format**: Float (0.0-3.0)
- **Default**: 1.0
- **Adjustment**: Based on confidence and outcome category

#### confidence_adjustment
- **Input Source**: Confidence scoring system
- **Format**: Float (0.0-2.0)
- **Calculation**: Signal strength × market conditions × historical success

#### delay_minutes
- **Input Source**: Timing optimization engine
- **Format**: Integer (0-60)
- **Determination**: Based on signal type and market volatility

#### max_attempts
- **Input Source**: Risk management rules
- **Format**: Integer (0-5)
- **Logic**: Decreases with consecutive losses, increases with wins

### Chain Tracking Table

#### chain_id
- **Input Source**: UUID generator with pattern
- **Format**: CH_{symbol}_{YYMMDD}_{sequence}
- **Example**: CH_EUR_240820_001

#### original_trade_id
- **Input Source**: Broker trade execution system
- **Format**: Integer trade ID from MT4/MT5

#### chain_trades
- **Input Source**: Counter of trades in reentry sequence
- **Format**: Integer
- **Increment**: +1 for each reentry execution

#### total_pnl
- **Input Source**: Cumulative P&L calculator
- **Format**: Float (currency units)
- **Update**: Real-time from trade closures

#### chain_status
- **Input Source**: Chain state machine
- **Format**: Enum string
- **Values**: ACTIVE, COMPLETED, STOPPED, ERROR

### Execution Audit Table

#### action_no
- **Input Source**: Outcome-to-action mapper
- **Format**: Integer (1-6)
- **Mapping**: Direct correlation to outcome values

#### entry_price
- **Input Source**: Broker execution price feed
- **Format**: Float with 5 decimal precision
- **Source**: Actual fill price from broker

#### size_lots
- **Input Source**: Position size calculator
- **Format**: Float (0.01-10.0)
- **Calculation**: base_size × size_multiplier × confidence_adjustment

#### confidence
- **Input Source**: Multi-factor confidence model
- **Format**: Float (0.0-1.0)
- **Inputs**: Signal strength, market volatility, time factors

#### exec_ms
- **Input Source**: Execution timer
- **Format**: Integer milliseconds
- **Measurement**: From decision to order confirmation

### Performance Metrics Table

#### execs/wins
- **Input Source**: Historical execution counter
- **Format**: Integer counts
- **Update**: Incremented on trade closure

#### total_pnl/avg_pnl
- **Input Source**: P&L aggregation system
- **Format**: Float currency values
- **Calculation**: Sum and average of closed trades

#### success_rate
- **Input Source**: Win/loss calculator
- **Format**: Float (0.0-1.0)
- **Formula**: wins ÷ total_executions

#### sharpe
- **Input Source**: Risk-adjusted return calculator
- **Format**: Float (-3.0 to +3.0)
- **Formula**: (avg_return - risk_free_rate) ÷ std_deviation

## Governance Controls

### EA Input Name
- **Input Source**: MetaTrader EA parameter names
- **Format**: String matching EA input variables
- **Purpose**: Maps external controls to internal parameters

### CSV Column
- **Input Source**: Data file column headers
- **Format**: String matching CSV column names
- **Purpose**: Links file data to processing logic

### Default
- **Input Source**: System configuration defaults
- **Format**: String representation of default values
- **Application**: Used when input validation fails

### Range/Rule
- **Input Source**: Validation rule definitions
- **Format**: String describing constraints
- **Examples**: "0.01-10.0", "ENUM[HIGH,MED,LOW]"

### Enforcement Point
- **Input Source**: Code location identifiers
- **Format**: String describing where validation occurs
- **Purpose**: Defines when/where rules are applied

### Failure Action
- **Input Source**: Error handling specifications
- **Format**: String describing failure response
- **Examples**: "USE_DEFAULT", "SKIP_TRADE", "ALERT_USER"

## Data Flow Summary

1. **Market Data** → Economic calendar and price feeds
2. **Signal Generation** → Classification into signal types and outcomes
3. **Context Analysis** → Future/past proximity determination
4. **Decision Engine** → Reentry/end decisions with parameters
5. **Execution System** → Trade placement and tracking
6. **Performance Analytics** → Historical analysis and optimization
7. **Governance Layer** → Validation and control enforcement

Each column header represents a specific data point in this flow, with inputs sourced from the corresponding system component and processed according to defined rules and validations.