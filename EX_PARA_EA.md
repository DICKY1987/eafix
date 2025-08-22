## 1. REQUIRED PARAMETERS
- `parameter_set_id`: Unique identifier for parameter set
- `name`: Human-readable parameter set name
- `global_risk_percent`: Base account risk percentage per trade (REQUIRED)
- `stop_loss_pips`: Stop loss distance in pips
- `take_profit_pips`: Take profit distance in pips
- `entry_order_type`: "MARKET", "PENDING", "STRADDLE"
## 3. STOP LOSS & TAKE PROFIT CONFIGURATION
- `stop_loss_method`: "FIXED", "ATR_MULTIPLE", "PERCENT"
- `atr_stop_multiplier`: ATR multiplication factor for SL
- `max_stop_loss_pips`: Maximum SL distance allowed
- `take_profit_method`: "FIXED", "RR_RATIO", "ATR_MULTIPLE"
- `risk_reward_ratio`: Risk-reward ratio target
- `partial_tp_levels`: Percentages for partial TP closures

### Advanced Trailing Stop Options
- `use_trailing_stop`: Enable/disable trailing stops
- `trailing_stop_method`: "CONTINUOUS", "STEPPED"
- `trailing_stop_pips`: Distance for trailing stop
- `trailing_step_pips`: Step size for trailing updates
- `trailing_start_pips`: Profit level to start trailing
- `trailing_step_size_pips`: Size of each trailing step
- `trailing_initial_distance_pips`: Initial trailing distance
- `trailing_step_trigger_pips`: Movement required to move trailing stop
- `breakeven_trigger_pips`: Profit level to move SL to breakeven
- `breakeven_plus_pips`: Move SL to breakeven + X pips
- `dynamic_trail_adjustment`: Switch trailing values based on profit
- `initial_trail_distance`: Starting trailing distance
- `adjusted_trail_distance`: Modified distance after X pips profit
- `trail_trigger_pips`: Profit level to switch trailing modes

## 4. ENTRY ORDER PARAMETERS

### Market Orders
- `market_slippage_pips`: Maximum acceptable slippage
- `market_retry_attempts`: Retry attempts on failure
- `market_retry_delay_ms`: Delay between retries
- `slippage_tolerance_pips`: Maximum acceptable slippage

### Pending Orders
- `entry_order_setup_type`: "STRADDLE", "BUY_STOP_ONLY", "SELL_STOP_ONLY"
- `pending_order_type`: Order type for single pending orders
- `pending_distance_pips`: Distance from current price
- `pending_expiration_minutes`: Order expiration time
- `pending_price_method`: "FIXED", "ATR", "SUPPORT_RESISTANCE"
- `atr_distance_multiplier`: ATR-based distance multiplier
- `pending_order_timeout_minutes`: Auto-delete pending orders after timeout
- `bias_direction`: -1 (bearish), 0 (neutral), 1 (bullish)
- `persist_bias_after_win`: Keep directional bias after profitable trades
- `bias_override_by_category`: Different bias rules per outcome category
- `trail_pending_orders`: Move pending orders with price movement

### Straddle Orders
- `straddle_distance_pips`: Distance from price for both legs
- `straddle_buy_order_type`: Order type for buy leg
- `straddle_sell_order_type`: Order type for sell leg
- `straddle_expiration_minutes`: Expiration for both legs
- `straddle_auto_cancel_opposite`: Cancel opposite when one fills
- `straddle_cancel_delay_seconds`: Delay before canceling
- `straddle_asymmetric`: Allow different distances
- `straddle_buy_distance_pips`: Buy leg distance (if asymmetric)
- `straddle_sell_distance_pips`: Sell leg distance (if asymmetric)
- `straddle_equal_lot_sizes`: Equal lot sizes for both legs
- `straddle_buy_lot_ratio`: Buy leg size ratio
- `straddle_sell_lot_ratio`: Sell leg size ratio
- `max_spread_pips`: Maximum spread allowed
- `entry_delay_seconds`: Delay before entering
emergency_stop_loss_percent`: Emergency stop at X% loss
- `emergency_close_all_trades`: Immediate closure of all positions
## 13. STATE MANAGEMENT & PERSISTENCE
- `current_ea_state`: "IDLE", "ORDERS_PLACED", "TRADE_TRIGGERED", "DISABLED"
- `restart_after_trade_close`: Auto-restart trading cycle
- `save_state_to_global_vars`: Persist settings between restarts
- `max_total_restarts`: Maximum total restarts allowed
- `reset_to_default_after_category1`: Reset parameters after Cat 1
- `max_consecutive_category1`: Max Cat 1 before pausing
- `inactivity_timeout_minutes`: Auto-remove EA if no activity
## 15. LOGGING & DEBUGGING
- `verbose_logging`: Detailed execution logging
- `log_to_file`: File-based logging for analysis
- `max_state_resets`: Limit unexpected state changes
