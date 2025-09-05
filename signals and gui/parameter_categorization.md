# EA Parameters Categorized by Input Type

## 🔵 BINARY/BOOLEAN PARAMETERS (On/Off, True/False)

### Advanced Trailing Stop Options
- `use_trailing_stop`: Enable/disable trailing stops
- `dynamic_trail_adjustment`: Switch trailing values based on profit
- `breakeven_trigger_pips`: Move SL to breakeven (enabled when > 0)

### Pending Orders  
- `persist_bias_after_win`: Keep directional bias after profitable trades
- `trail_pending_orders`: Move pending orders with price movement

### Straddle Orders
- `straddle_auto_cancel_opposite`: Cancel opposite when one fills
- `straddle_asymmetric`: Allow different distances for buy/sell legs
- `straddle_equal_lot_sizes`: Equal lot sizes for both legs
- `emergency_close_all_trades`: Immediate closure of all positions

### State Management & Persistence
- `restart_after_trade_close`: Auto-restart trading cycle
- `save_state_to_global_vars`: Persist settings between restarts
- `reset_to_default_after_category1`: Reset parameters after Cat 1

### Logging & Debugging
- `verbose_logging`: Detailed execution logging
- `log_to_file`: File-based logging for analysis

---

## 🔢 NUMERIC PARAMETERS (Number Input Required)

### Required Parameters
- `global_risk_percent`: Base account risk percentage per trade (e.g., 1.0, 2.5)
- `stop_loss_pips`: Stop loss distance in pips (e.g., 20, 35)
- `take_profit_pips`: Take profit distance in pips (e.g., 40, 60)

### Stop Loss & Take Profit Configuration
- `atr_stop_multiplier`: ATR multiplication factor for SL (e.g., 2.0, 1.5)
- `max_stop_loss_pips`: Maximum SL distance allowed (e.g., 200)
- `risk_reward_ratio`: Risk-reward ratio target (e.g., 2.0, 3.0)

### Advanced Trailing Stop Options
- `trailing_stop_pips`: Distance for trailing stop (e.g., 20)
- `trailing_step_pips`: Step size for trailing updates (e.g., 5)
- `trailing_start_pips`: Profit level to start trailing (e.g., 10)
- `trailing_step_size_pips`: Size of each trailing step (e.g., 5)
- `trailing_initial_distance_pips`: Initial trailing distance (e.g., 20)
- `trailing_step_trigger_pips`: Movement required to move trailing stop (e.g., 10)
- `breakeven_plus_pips`: Move SL to breakeven + X pips (e.g., 1)
- `initial_trail_distance`: Starting trailing distance (e.g., 20)
- `adjusted_trail_distance`: Modified distance after X pips profit (e.g., 10)
- `trail_trigger_pips`: Profit level to switch trailing modes (e.g., 30)

### Market Orders
- `market_slippage_pips`: Maximum acceptable slippage (e.g., 3)
- `market_retry_attempts`: Retry attempts on failure (e.g., 3)
- `market_retry_delay_ms`: Delay between retries (e.g., 300)
- `slippage_tolerance_pips`: Maximum acceptable slippage (e.g., 3)

### Pending Orders
- `pending_distance_pips`: Distance from current price (e.g., 15)
- `pending_expiration_minutes`: Order expiration time (e.g., 120)
- `atr_distance_multiplier`: ATR-based distance multiplier (e.g., 1.5)
- `pending_order_timeout_minutes`: Auto-delete pending orders after timeout (e.g., 180)
- `bias_direction`: -1 (bearish), 0 (neutral), 1 (bullish)
- `max_consecutive_category1`: Max Cat 1 before pausing (e.g., 2)

### Straddle Orders
- `straddle_distance_pips`: Distance from price for both legs (e.g., 20)
- `straddle_expiration_minutes`: Expiration for both legs (e.g., 180)
- `straddle_cancel_delay_seconds`: Delay before canceling (e.g., 2)
- `straddle_buy_distance_pips`: Buy leg distance (if asymmetric) (e.g., 18)
- `straddle_sell_distance_pips`: Sell leg distance (if asymmetric) (e.g., 22)
- `straddle_buy_lot_ratio`: Buy leg size ratio (e.g., 1.0)
- `straddle_sell_lot_ratio`: Sell leg size ratio (e.g., 1.0)
- `max_spread_pips`: Maximum spread allowed (e.g., 30)
- `entry_delay_seconds`: Delay before entering (e.g., 0)
- `emergency_stop_loss_percent`: Emergency stop at X% loss (e.g., 35.0)

### State Management & Persistence
- `max_total_restarts`: Maximum total restarts allowed (e.g., 3)
- `inactivity_timeout_minutes`: Auto-remove EA if no activity (e.g., 240)

### Logging & Debugging
- `max_state_resets`: Limit unexpected state changes (e.g., 10)

---

## 📋 CHOICE/ENUM PARAMETERS (Multiple Predefined Options)

### Required Parameters
- `entry_order_type`: 
  - **Options:** "MARKET", "PENDING", "STRADDLE"

### Stop Loss & Take Profit Configuration
- `stop_loss_method`: 
  - **Options:** "FIXED", "ATR_MULTIPLE", "PERCENT"
- `take_profit_method`: 
  - **Options:** "FIXED", "RR_RATIO", "ATR_MULTIPLE"

### Advanced Trailing Stop Options
- `trailing_stop_method`: 
  - **Options:** "CONTINUOUS", "STEPPED"

### Pending Orders
- `entry_order_setup_type`: 
  - **Options:** "STRADDLE", "BUY_STOP_ONLY", "SELL_STOP_ONLY"
- `pending_price_method`: 
  - **Options:** "FIXED", "ATR", "SUPPORT_RESISTANCE"

### Straddle Orders
- `straddle_buy_order_type`: 
  - **Options:** OP_BUYSTOP, OP_BUYLIMIT
- `straddle_sell_order_type**: 
  - **Options:** OP_SELLSTOP, OP_SELLLIMIT

### State Management & Persistence
- `current_ea_state`: 
  - **Options:** "IDLE", "ORDERS_PLACED", "TRADE_TRIGGERED", "DISABLED"

---

## 📝 STRING/TEXT PARAMETERS (Free Text Input)

### Required Parameters
- `parameter_set_id`: Unique identifier for parameter set (e.g., "PS_001")
- `name`: Human-readable parameter set name (e.g., "BaselineSet")

### Stop Loss & Take Profit Configuration
- `partial_tp_levels`: Percentages for partial TP closures (e.g., "50|80")

### Pending Orders
- `bias_override_by_category`: Different bias rules per outcome category (e.g., "CAT1=-1|CAT2=0")

---

## 💡 Parameter Type Usage Summary

- **Binary (15 parameters)**: Simple on/off switches for features
- **Numeric (35 parameters)**: Require specific number values (pips, percentages, timeouts)
- **Choice (9 parameters)**: Select from predefined options
- **String (4 parameters)**: Free text input for identifiers and configurations

This categorization helps in designing user interfaces where:
- **Binary** parameters use checkboxes/toggles
- **Numeric** parameters use number input fields with validation
- **Choice** parameters use dropdown menus/radio buttons
- **String** parameters use text input fields