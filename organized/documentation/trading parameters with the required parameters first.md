List all the trading parameters with the required parameters first then the others in a logical order

Edit
Complete Trading Parameters List
1. Required Parameters (Must be specified for every parameter set)
Core Position Parameters
python
# REQUIRED - Basic trade setup
parameter_set_id: int           # Unique identifier for this parameter set
name: str                       # Human-readable name (e.g., "Conservative", "Aggressive")
lot_size: float                 # Base position size (e.g., 0.01, 0.1, 1.0)
stop_loss_pips: int            # Stop loss distance in pips
take_profit_pips: int          # Take profit distance in pips

# REQUIRED - Entry method
entry_order_type: str          # "MARKET", "PENDING", "STRADDLE"
2. Risk Management Parameters
Position Sizing & Risk Controls
python
# Position sizing
risk_percent: float = 1.0              # Percentage of account to risk per trade
max_lot_size: float = 1.0              # Maximum allowed lot size
min_lot_size: float = 0.01             # Minimum allowed lot size
position_sizing_method: str = "FIXED"   # "FIXED", "RISK_BASED", "PERCENT_EQUITY"

# Position limits
max_positions_total: int = 3           # Max open positions across all pairs
max_positions_per_pair: int = 1        # Max positions per currency pair
max_positions_same_direction: int = 5   # Max positions in same direction
correlation_limit: float = 0.8         # Max correlation between open positions

# Daily/weekly limits
daily_loss_limit: float = 500.0        # Max daily loss in account currency
daily_profit_target: float = 1000.0    # Daily profit target
max_daily_trades: int = 10             # Maximum trades per day
weekly_loss_limit: float = 2000.0      # Maximum weekly loss
Stop Loss & Take Profit Configuration
python
# Stop loss methods
stop_loss_method: str = "FIXED"        # "FIXED", "ATR_MULTIPLE", "PERCENT"
atr_stop_multiplier: float = 2.0       # If using ATR-based SL
max_stop_loss_pips: int = 100          # Maximum SL distance allowed

# Take profit methods
take_profit_method: str = "FIXED"      # "FIXED", "RR_RATIO", "ATR_MULTIPLE"
risk_reward_ratio: float = 2.0         # R:R ratio (e.g., 1:2 = 2.0)
partial_tp_levels: list = [50, 75]     # Percentages for partial TP

# Trailing stop configuration
use_trailing_stop: bool = False        # Enable/disable trailing
trailing_stop_pips: int = 30           # Distance for trailing stop
trailing_step_pips: int = 5            # Step size for trailing updates
trailing_start_pips: int = 20          # Profit level to start trailing
3. Entry Order Parameters
Market Order Settings
python
# Market execution
market_slippage_pips: int = 3          # Maximum acceptable slippage
market_retry_attempts: int = 3         # Retry attempts on failure
market_retry_delay_ms: int = 500       # Delay between retries
Single Pending Order Settings
python
# Pending order configuration
pending_order_type: str = "BUY_STOP"   # BUY_STOP, SELL_STOP, BUY_LIMIT, SELL_LIMIT
pending_distance_pips: int = 10        # Distance from current price
pending_expiration_minutes: int = 60   # Order expiration time
pending_price_method: str = "FIXED"    # "FIXED", "ATR", "SUPPORT_RESISTANCE"
atr_distance_multiplier: float = 1.5   # If using ATR-based distance
Straddle Order Settings
python
# Basic straddle configuration
straddle_distance_pips: int = 15           # Distance from price for both legs
straddle_buy_order_type: str = "BUY_STOP"  # Order type for buy leg
straddle_sell_order_type: str = "SELL_STOP" # Order type for sell leg
straddle_expiration_minutes: int = 120     # Expiration for both legs
straddle_auto_cancel_opposite: bool = True # Cancel opposite when one fills
straddle_cancel_delay_seconds: int = 2     # Delay before canceling

# Advanced straddle options
straddle_asymmetric: bool = False          # Allow different distances
straddle_buy_distance_pips: int = 15       # Buy leg distance (if asymmetric)
straddle_sell_distance_pips: int = 15      # Sell leg distance (if asymmetric)
straddle_equal_lot_sizes: bool = True      # Equal lot sizes for both legs
straddle_buy_lot_ratio: float = 1.0        # Buy leg size ratio (if not equal)
straddle_sell_lot_ratio: float = 1.0       # Sell leg size ratio (if not equal)
4. Reentry-Specific Parameters
Size Adjustment for Reentries
python
# Size modifications (relative to original trade)
size_multiplier: float = 1.0               # Base size multiplier for reentries
size_adjustment_method: str = "MULTIPLY"    # "MULTIPLY", "ADD_LOTS", "FIBONACCI"
fibonacci_sequence: list = [1,1,2,3,5]     # For Fibonacci sizing
max_reentry_size_multiplier: float = 3.0   # Cap on size increases

# Progressive sizing
progressive_sizing: bool = False           # Increase/decrease size each generation
progressive_multiplier: float = 1.2       # Multiply by this each reentry
size_cap_per_generation: dict = {          # Size caps by generation
    1: 2.0, 2: 1.5, 3: 1.0
}
Timing and Delays for Reentries
python
# Delay controls
base_delay_seconds: int = 30               # Base delay before reentry
progressive_delay: bool = False            # Increase delay each generation
delay_multiplier: float = 1.5             # Multiply delay each reentry
max_delay_minutes: int = 60                # Maximum delay allowed
random_delay_range: int = 10               # ±X seconds of randomness
Entry Modifications for Reentries
python
# Entry adjustments
confidence_adjustment: float = 1.0         # Multiply original confidence
min_reentry_confidence: float = 0.6        # Minimum confidence for reentries
confidence_decay_per_generation: float = 0.1 # Reduce confidence each reentry
entry_offset_pips: int = 0                 # Offset entry price by X pips
use_limit_orders_for_reentry: bool = False # Use limits instead of market
limit_order_offset_pips: int = 5           # Distance for limit orders
5. Market Condition Parameters
Economic Event Controls
python
# News trading
trade_during_news: bool = True             # Allow trading during news
news_volatility_multiplier: float = 1.0   # Adjust size during news
high_impact_news_action: str = "NORMAL"   # "PAUSE", "REDUCE_SIZE", "NORMAL"
pre_news_cutoff_minutes: int = 30          # Stop new entries before news
post_news_wait_minutes: int = 15           # Wait after news to resume

# Event clustering
cluster_sensitivity: float = 1.0           # How clustering affects decisions
isolated_event_bonus: float = 1.0          # Size bonus for isolated events
cluster_size_reduction: float = 0.8        # Size reduction in clusters
Session-Based Adjustments
python
# Session timing
asia_session_multiplier: float = 1.0       # Size adjustment for Asia
europe_session_multiplier: float = 1.0     # Size adjustment for Europe
us_session_multiplier: float = 1.0         # Size adjustment for US
overlap_period_bonus: float = 1.0          # Bonus during overlaps

# Trading hours
trading_hours_start: str = "00:00"         # Start time (24h format)
trading_hours_end: str = "23:59"           # End time (24h format)
weekend_trading: bool = False              # Allow weekend trading
holiday_trading: bool = True               # Allow holiday trading
Volatility Controls
python
# Volatility adjustments
low_volatility_action: str = "NORMAL"      # "PAUSE", "INCREASE_SIZE", "NORMAL"
high_volatility_action: str = "NORMAL"     # "PAUSE", "REDUCE_SIZE", "NORMAL"
volatility_threshold_low: float = 0.5      # ATR threshold for low vol
volatility_threshold_high: float = 2.0     # ATR threshold for high vol
volatility_size_multiplier: float = 1.0    # Size adjustment for volatility
6. Chain Management Parameters
Generation and Chain Controls
python
# Chain limits
max_reentry_generations: int = 3           # Maximum reentries allowed
stop_after_consecutive_losses: int = 2     # Stop after X losses in row
stop_after_drawdown_percent: float = 10.0 # Stop if chain drawdown > X%
max_chain_duration_hours: int = 24        # Force stop after X hours

# Performance-based controls
min_chain_profit_continue: float = 0.0    # Min profit to continue
max_chain_loss_stop: float = -200.0       # Max loss before stopping
chain_success_rate_threshold: float = 0.3 # Stop if success rate < X%
lookback_period_trades: int = 10           # Recent trades to evaluate
7. Entry Conditions & Filters
Market Entry Conditions
python
# Entry requirements
confidence_threshold: float = 0.7         # Minimum confidence to enter
max_spread_pips: int = 5                  # Maximum spread allowed
entry_delay_seconds: int = 0              # Delay before entering
slippage_tolerance_pips: int = 3          # Maximum acceptable slippage

# Market filters
min_volatility_required: float = 0.0     # Minimum ATR to trade
max_volatility_allowed: float = 999.0    # Maximum ATR to trade
avoid_news_minutes: int = 0               # Minutes to avoid around news
require_trend_alignment: bool = False     # Require trend confirmation
8. Safety & Emergency Controls
Emergency Stop Parameters
python
# Emergency controls
emergency_stop_loss_percent: float = 20.0    # Emergency stop at X% loss
correlation_emergency_stop: float = 0.95     # Stop if correlation > X
drawdown_emergency_stop: float = 15.0        # Stop if drawdown > X%
consecutive_loss_emergency: int = 5          # Emergency stop after X losses

# Recovery mode
recovery_mode_trigger: float = -10.0         # Enter recovery at X% loss
recovery_mode_size_multiplier: float = 0.5   # Size in recovery mode
recovery_mode_max_trades: int = 3            # Max trades in recovery
recovery_exit_profit_target: float = 5.0     # Profit to exit recovery
Circuit Breakers
python
# System protection
max_trades_per_hour: int = 10             # Limit trades per hour
max_trades_per_minute: int = 2            # Limit trades per minute
cool_down_after_loss_streak: int = 3      # Cool down after X losses
cool_down_duration_minutes: int = 30      # Duration of cool down
force_break_after_hours: int = 8          # Force break after X hours
forced_break_duration_minutes: int = 60   # Duration of forced break
9. Metadata & Tracking
Parameter Set Information
python
# Identification and tracking
description: str = ""                     # Detailed description
created_date: datetime = None             # When created
updated_date: datetime = None             # Last modification
created_by: str = ""                      # Creator name
version: str = "1.0"                      # Version number
active: bool = True                       # Is this set active?
backtest_verified: bool = False           # Has been backtested?
live_verified: bool = False               # Has been live tested?

# Performance tracking (read-only, updated by system)
total_executions: int = 0                 # Times this set was used
successful_executions: int = 0            # Successful trades
total_pnl: float = 0.0                   # Total P&L generated
last_execution: datetime = None           # Last time used
avg_execution_time_ms: int = 0           # Average execution time
10. Example Complete Parameter Set
python
EXAMPLE_AGGRESSIVE_MOMENTUM_SET = {
    # REQUIRED
    "parameter_set_id": 8,
    "name": "Aggressive Momentum",
    "lot_size": 0.1,
    "stop_loss_pips": 30,
    "take_profit_pips": 90,
    "entry_order_type": "STRADDLE",
    
    # Risk Management
    "risk_percent": 2.0,
    "max_lot_size": 0.5,
    "max_positions_total": 5,
    "daily_loss_limit": 500.0,
    
    # Entry Orders
    "straddle_distance_pips": 20,
    "straddle_auto_cancel_opposite": True,
    "straddle_expiration_minutes": 60,
    
    # Reentry
    "size_multiplier": 1.5,
    "base_delay_seconds": 0,
    "confidence_adjustment": 1.1,
    "max_reentry_generations": 3,
    
    # Market Conditions
    "trade_during_news": True,
    "news_volatility_multiplier": 1.2,
    "high_volatility_action": "NORMAL",
    
    # Safety
    "emergency_stop_loss_percent": 15.0,
    "consecutive_loss_emergency": 4,
    
    # Metadata
    "description": "High-risk momentum strategy with straddle entries",
    "active": True,
    "version": "2.1"
}
This structure ensures you have complete control over every aspect of trading behavior while maintaining logical organization and required vs. optional parameter separation.




Create document that list each parameter with a description in plain English

Edit
Trading Parameter Reference Guide
Complete Parameter Descriptions in Plain English
1. REQUIRED PARAMETERS
These must be set for every parameter set

parameter_set_id (Number)
A unique number that identifies this specific set of trading rules. Like an ID card number - no two parameter sets can have the same number.

name (Text)
A simple name for this parameter set that humans can understand, like "Conservative" or "Aggressive Momentum" or "News Scalper."

lot_size (Decimal number)
How big your trades will be. 0.01 = micro lot, 0.1 = mini lot, 1.0 = standard lot. This is your default trade size before any adjustments.

stop_loss_pips (Whole number)
How far the price can move against you before the trade automatically closes to prevent bigger losses. Measured in pips (smallest price movements).

take_profit_pips (Whole number)
How far the price needs to move in your favor before the trade automatically closes to lock in profits. Also measured in pips.

entry_order_type (Text choice)
How you want to enter trades:

"MARKET" = Buy/sell immediately at current price
"PENDING" = Place an order that waits for price to reach a specific level
"STRADDLE" = Place both buy and sell orders above and below current price, cancel the one that doesn't get hit
2. RISK MANAGEMENT PARAMETERS
risk_percent (Decimal number, default: 1.0)
What percentage of your total account you're willing to risk on each trade. 1.0 = 1% of account, 2.0 = 2% of account.

max_lot_size (Decimal number, default: 1.0)
The biggest trade size you'll ever allow, no matter what the calculations say. Safety limit to prevent huge trades.

min_lot_size (Decimal number, default: 0.01)
The smallest trade size allowed. Prevents trades that are too tiny to be worthwhile.

position_sizing_method (Text choice, default: "FIXED")
How to calculate trade size:

"FIXED" = Always use the same lot size
"RISK_BASED" = Calculate size based on risk_percent
"PERCENT_EQUITY" = Use a percentage of current account balance
max_positions_total (Whole number, default: 3)
Maximum number of trades you can have open at the same time across all currency pairs.

max_positions_per_pair (Whole number, default: 1)
Maximum number of trades on the same currency pair (like EURUSD) at one time.

max_positions_same_direction (Whole number, default: 5)
Maximum number of buy trades OR sell trades you can have open at once.

correlation_limit (Decimal number, default: 0.8)
Prevents opening trades on currency pairs that move too similarly. 0.8 means if two pairs move together 80% of the time, don't trade both.

daily_loss_limit (Decimal number, default: 500.0)
Maximum amount of money you're willing to lose in one day. Trading stops when this limit is hit.

daily_profit_target (Decimal number, default: 1000.0)
Daily profit goal. Some strategies stop trading when this target is reached.

max_daily_trades (Whole number, default: 10)
Maximum number of trades allowed in one day. Prevents overtrading.

weekly_loss_limit (Decimal number, default: 2000.0)
Maximum amount you're willing to lose in one week. Bigger safety net than daily limit.

3. STOP LOSS & TAKE PROFIT SETTINGS
stop_loss_method (Text choice, default: "FIXED")
How to set stop losses:

"FIXED" = Always use the same pip distance
"ATR_MULTIPLE" = Base distance on market volatility
"PERCENT" = Use a percentage of entry price
atr_stop_multiplier (Decimal number, default: 2.0)
If using ATR method, multiply the volatility measurement by this number. Higher = wider stop loss.

max_stop_loss_pips (Whole number, default: 100)
The furthest away your stop loss can ever be, regardless of what the calculation says.

take_profit_method (Text choice, default: "FIXED")
How to set take profits:

"FIXED" = Always use the same pip distance
"RR_RATIO" = Based on risk-reward ratio
"ATR_MULTIPLE" = Based on market volatility
risk_reward_ratio (Decimal number, default: 2.0)
How much profit you want compared to your risk. 2.0 means if you risk $100, you want to make $200.

partial_tp_levels (List of numbers, default: [50, 75])
Close portions of your trade at these profit percentages. [50, 75] means close half at 50% of target, three-quarters at 75%.

use_trailing_stop (True/False, default: False)
Whether to move your stop loss closer to current price as the trade becomes more profitable.

trailing_stop_pips (Whole number, default: 30)
How many pips behind the current price to keep your trailing stop.

trailing_step_pips (Whole number, default: 5)
How many pips the price must move in your favor before the trailing stop moves.

trailing_start_pips (Whole number, default: 20)
How much profit you need before trailing stop starts working.

4. ENTRY ORDER PARAMETERS
market_slippage_pips (Whole number, default: 3)
For market orders, how much worse price you'll accept compared to what you expected.

market_retry_attempts (Whole number, default: 3)
If a market order fails, how many times to try again.

market_retry_delay_ms (Whole number, default: 500)
How many milliseconds to wait between retry attempts.

pending_order_type (Text choice, default: "BUY_STOP")
For single pending orders, what type:

"BUY_STOP" = Buy when price goes above a level
"SELL_STOP" = Sell when price goes below a level
"BUY_LIMIT" = Buy when price comes down to a level
"SELL_LIMIT" = Sell when price comes up to a level
pending_distance_pips (Whole number, default: 10)
How many pips away from current price to place your pending order.

pending_expiration_minutes (Whole number, default: 60)
How long to wait for a pending order to get filled before canceling it.

pending_price_method (Text choice, default: "FIXED")
How to calculate where to place pending orders:

"FIXED" = Always same distance from current price
"ATR" = Based on market volatility
"SUPPORT_RESISTANCE" = Based on chart levels
atr_distance_multiplier (Decimal number, default: 1.5)
If using ATR method for pending orders, multiply volatility by this number.

5. STRADDLE ORDER PARAMETERS
straddle_distance_pips (Whole number, default: 15)
How many pips above and below current price to place your buy and sell orders.

straddle_buy_order_type (Text choice, default: "BUY_STOP")
What type of order to use for the buy side of the straddle.

straddle_sell_order_type (Text choice, default: "SELL_STOP")
What type of order to use for the sell side of the straddle.

straddle_expiration_minutes (Whole number, default: 120)
How long to wait for one side of the straddle to get hit before canceling both orders.

straddle_auto_cancel_opposite (True/False, default: True)
When one side of the straddle gets filled, automatically cancel the other side.

straddle_cancel_delay_seconds (Whole number, default: 2)
How many seconds to wait after one side fills before canceling the other side.

straddle_asymmetric (True/False, default: False)
Allow different distances for buy and sell sides of the straddle.

straddle_buy_distance_pips (Whole number, default: 15)
If using asymmetric, how far above current price to place buy order.

straddle_sell_distance_pips (Whole number, default: 15)
If using asymmetric, how far below current price to place sell order.

straddle_equal_lot_sizes (True/False, default: True)
Use the same trade size for both sides of the straddle.

straddle_buy_lot_ratio (Decimal number, default: 1.0)
If not using equal sizes, what fraction of total size to use for buy side.

straddle_sell_lot_ratio (Decimal number, default: 1.0)
If not using equal sizes, what fraction of total size to use for sell side.

6. REENTRY PARAMETERS
size_multiplier (Decimal number, default: 1.0)
How to adjust trade size for reentries compared to original trade. 1.0 = same size, 2.0 = double size, 0.5 = half size.

size_adjustment_method (Text choice, default: "MULTIPLY")
How to calculate reentry trade size:

"MULTIPLY" = Multiply original size by the multiplier
"ADD_LOTS" = Add fixed lot amounts
"FIBONACCI" = Use Fibonacci sequence for sizing
fibonacci_sequence (List of numbers, default: [1,1,2,3,5])
If using Fibonacci method, the sequence of multipliers to use for each reentry.

max_reentry_size_multiplier (Decimal number, default: 3.0)
The biggest size multiplier allowed, to prevent trades from getting too large.

progressive_sizing (True/False, default: False)
Whether to change the size multiplier with each new reentry.

progressive_multiplier (Decimal number, default: 1.2)
If using progressive sizing, multiply the size by this amount each reentry.

size_cap_per_generation (Dictionary, default: {1: 2.0, 2: 1.5, 3: 1.0})
Maximum size multiplier allowed for each reentry level.

base_delay_seconds (Whole number, default: 30)
How many seconds to wait before placing a reentry trade.

progressive_delay (True/False, default: False)
Whether to increase the delay time with each reentry.

delay_multiplier (Decimal number, default: 1.5)
If using progressive delay, multiply wait time by this amount each reentry.

max_delay_minutes (Whole number, default: 60)
The longest you'll ever wait before placing a reentry, regardless of calculations.

random_delay_range (Whole number, default: 10)
Add random variation to delay times, plus or minus this many seconds.

confidence_adjustment (Decimal number, default: 1.0)
Multiply the original trade's confidence score by this amount for reentries.

min_reentry_confidence (Decimal number, default: 0.6)
Don't place reentry trades if confidence falls below this level.

confidence_decay_per_generation (Decimal number, default: 0.1)
Reduce confidence by this amount with each reentry level.

entry_offset_pips (Whole number, default: 0)
Move the entry price by this many pips away from the calculated price.

use_limit_orders_for_reentry (True/False, default: False)
Use limit orders instead of market orders for reentry trades.

limit_order_offset_pips (Whole number, default: 5)
If using limit orders for reentries, how many pips away from current price to place them.

7. MARKET CONDITION PARAMETERS
trade_during_news (True/False, default: True)
Whether to allow trading during major economic news announcements.

news_volatility_multiplier (Decimal number, default: 1.0)
Adjust trade size during news by this multiplier. 0.5 = half size, 2.0 = double size.

high_impact_news_action (Text choice, default: "NORMAL")
What to do during high-impact news:

"PAUSE" = Stop all trading
"REDUCE_SIZE" = Use smaller trade sizes
"NORMAL" = Trade normally
pre_news_cutoff_minutes (Whole number, default: 30)
Stop opening new trades this many minutes before major news.

post_news_wait_minutes (Whole number, default: 15)
Wait this many minutes after news before resuming normal trading.

cluster_sensitivity (Decimal number, default: 1.0)
How much to adjust behavior when multiple economic events are clustered together.

isolated_event_bonus (Decimal number, default: 1.0)
Size multiplier for events that are isolated from other events.

cluster_size_reduction (Decimal number, default: 0.8)
Size multiplier when events are clustered together.

asia_session_multiplier (Decimal number, default: 1.0)
Adjust trade size during Asian trading session.

europe_session_multiplier (Decimal number, default: 1.0)
Adjust trade size during European trading session.

us_session_multiplier (Decimal number, default: 1.0)
Adjust trade size during US trading session.

overlap_period_bonus (Decimal number, default: 1.0)
Size multiplier when major trading sessions overlap.

trading_hours_start (Time, default: "00:00")
What time to start trading each day (24-hour format).

trading_hours_end (Time, default: "23:59")
What time to stop trading each day (24-hour format).

weekend_trading (True/False, default: False)
Whether to trade during weekends (if market is open).

holiday_trading (True/False, default: True)
Whether to trade during holidays.

low_volatility_action (Text choice, default: "NORMAL")
What to do when market volatility is low:

"PAUSE" = Stop trading
"INCREASE_SIZE" = Use bigger trades
"NORMAL" = Trade normally
high_volatility_action (Text choice, default: "NORMAL")
What to do when market volatility is high:

"PAUSE" = Stop trading
"REDUCE_SIZE" = Use smaller trades
"NORMAL" = Trade normally
volatility_threshold_low (Decimal number, default: 0.5)
ATR value below which market is considered "low volatility."

volatility_threshold_high (Decimal number, default: 2.0)
ATR value above which market is considered "high volatility."

volatility_size_multiplier (Decimal number, default: 1.0)
General adjustment to trade size based on current volatility.

8. CHAIN MANAGEMENT PARAMETERS
max_reentry_generations (Whole number, default: 3)
Maximum number of reentry trades allowed after the original trade. 3 means original + 3 reentries = 4 total trades max.

stop_after_consecutive_losses (Whole number, default: 2)
Stop the reentry chain after this many losing trades in a row.

stop_after_drawdown_percent (Decimal number, default: 10.0)
Stop the reentry chain if total losses reach this percentage.

max_chain_duration_hours (Whole number, default: 24)
Force stop the entire reentry chain after this many hours, regardless of results.

min_chain_profit_continue (Decimal number, default: 0.0)
Minimum profit needed to continue the reentry chain.

max_chain_loss_stop (Decimal number, default: -200.0)
Stop the chain if total losses reach this dollar amount.

chain_success_rate_threshold (Decimal number, default: 0.3)
Stop the chain if success rate drops below this percentage (0.3 = 30%).

lookback_period_trades (Whole number, default: 10)
How many recent trades to look at when calculating success rate.

9. ENTRY CONDITIONS & FILTERS
confidence_threshold (Decimal number, default: 0.7)
Minimum confidence score required to open any trade. 0.7 = 70% confidence.

max_spread_pips (Whole number, default: 5)
Don't trade if the spread (difference between buy and sell price) is wider than this.

entry_delay_seconds (Whole number, default: 0)
Always wait this many seconds after getting a signal before placing the trade.

slippage_tolerance_pips (Whole number, default: 3)
Maximum difference between expected price and actual fill price you'll accept.

min_volatility_required (Decimal number, default: 0.0)
Don't trade if market volatility (ATR) is below this level.

max_volatility_allowed (Decimal number, default: 999.0)
Don't trade if market volatility (ATR) is above this level.

avoid_news_minutes (Whole number, default: 0)
Don't trade this many minutes before and after any economic news.

require_trend_alignment (True/False, default: False)
Only trade if the signal agrees with the overall market trend.

10. SAFETY & EMERGENCY CONTROLS
emergency_stop_loss_percent (Decimal number, default: 20.0)
Stop all trading if account loses this percentage of total value.

correlation_emergency_stop (Decimal number, default: 0.95)
Stop trading if open positions become too correlated (moving together).

drawdown_emergency_stop (Decimal number, default: 15.0)
Stop trading if account drawdown reaches this percentage.

consecutive_loss_emergency (Whole number, default: 5)
Stop all trading after this many losing trades in a row.

recovery_mode_trigger (Decimal number, default: -10.0)
Enter "recovery mode" when account loses this percentage.

recovery_mode_size_multiplier (Decimal number, default: 0.5)
In recovery mode, multiply all trade sizes by this amount.

recovery_mode_max_trades (Whole number, default: 3)
Maximum trades allowed while in recovery mode.

recovery_exit_profit_target (Decimal number, default: 5.0)
Profit percentage needed to exit recovery mode.

max_trades_per_hour (Whole number, default: 10)
Don't place more than this many trades in one hour.

max_trades_per_minute (Whole number, default: 2)
Don't place more than this many trades in one minute.

cool_down_after_loss_streak (Whole number, default: 3)
Force a break after this many losing trades in a row.

cool_down_duration_minutes (Whole number, default: 30)
How long the forced break lasts.

force_break_after_hours (Whole number, default: 8)
Force a break after trading continuously for this many hours.

forced_break_duration_minutes (Whole number, default: 60)
How long the forced break lasts after continuous trading.

11. INFORMATION & TRACKING PARAMETERS
description (Text, default: "")
A longer explanation of what this parameter set is designed to do.

created_date (Date/Time, default: None)
When this parameter set was first created.

updated_date (Date/Time, default: None)
When this parameter set was last modified.

created_by (Text, default: "")
Who created this parameter set.

version (Text, default: "1.0")
Version number to track changes over time.

active (True/False, default: True)
Whether this parameter set can currently be used for trading.

backtest_verified (True/False, default: False)
Whether this parameter set has been tested on historical data.

live_verified (True/False, default: False)
Whether this parameter set has been tested with real money.

READ-ONLY PERFORMANCE PARAMETERS
These are automatically updated by the system

total_executions (Whole number, default: 0)
How many times this parameter set has been used.

successful_executions (Whole number, default: 0)
How many of those times resulted in profitable trades.

total_pnl (Decimal number, default: 0.0)
Total profit or loss generated by this parameter set.

last_execution (Date/Time, default: None)
The last time this parameter set was used.

avg_execution_time_ms (Whole number, default: 0)
Average time it takes to place trades using this parameter set.

This reference guide contains all parameters available in the trading system. Required parameters must be set, while others have sensible defaults that can be adjusted based on your trading strategy and risk tolerance.




The user should not be able to set the position size directly. User should set global risk parameter that is a percentage of account value. There should be a standard risk of loss per trade for example, let’s say 3%. All position sizing then is calculated from that there should be a parameter for risk adjustment that will allow the traitor to it or negative multiplier to the standard risk amount and that change and risk percentage loss relative to the account balance then determines the position size there needs to be a cap as well for the risk of loss portrayed and that needs to be 3.5% maximum that can be risk on any one trade that’s for the original trade in all entries we want to take the ability for the user to set position size and and create a situation where the user must focus on the potential risk

Edit
Revised Position Sizing System - Risk-Based Only
You're absolutely right! Direct position sizing creates dangerous situations. Here's the corrected risk-based system:

1. REMOVED PARAMETERS (No longer available to users)
python
# REMOVED - Users can no longer set these directly
# lot_size: float                 # REMOVED
# max_lot_size: float            # REMOVED  
# min_lot_size: float            # REMOVED
# position_sizing_method: str    # REMOVED (always risk-based now)
2. NEW REQUIRED RISK PARAMETERS
global_risk_percent (Decimal number, REQUIRED)
Description: The standard percentage of your account you're willing to lose on each trade. This is your baseline risk level that all position sizes are calculated from. Example: 3.0 means you're willing to risk 3% of your account on each trade Range: 0.1% to 3.5% maximum Default: None (must be set by user)

risk_adjustment_multiplier (Decimal number, default: 1.0)
Description: Adjusts the risk up or down from your global risk percentage. Multiply your global risk by this number to get the actual risk for this parameter set. Examples:

1.0 = Use exactly the global risk (3% × 1.0 = 3%)
0.5 = Use half the global risk (3% × 0.5 = 1.5%)
1.2 = Use 20% more risk (3% × 1.2 = 3.6% - but capped at 3.5%) Range: 0.1 to 1.17 maximum (to prevent exceeding 3.5% cap)
max_risk_cap_percent (Decimal number, SYSTEM ENFORCED: 3.5)
Description: The absolute maximum percentage of account that can be risked on any single trade. This is a hard limit that cannot be exceeded regardless of calculations. Value: Always 3.5% - cannot be changed by user Purpose: Safety limit to prevent catastrophic losses

3. CALCULATED POSITION SIZE PARAMETERS (Read-only)
calculated_lot_size (Decimal number, READ-ONLY)
Description: The actual lot size that will be used for trades, automatically calculated based on your risk settings, account balance, and stop loss distance. Formula: (Account Balance × Actual Risk %) ÷ (Stop Loss Pips × Pip Value) Updated: Automatically recalculated before each trade

actual_risk_percent (Decimal number, READ-ONLY)
Description: The final risk percentage being used after applying the risk adjustment multiplier and safety caps. Formula: MIN(global_risk_percent × risk_adjustment_multiplier, 3.5%) Example: If global_risk_percent = 3.0% and risk_adjustment_multiplier = 1.3, then actual_risk_percent = 3.5% (capped)

risk_amount_dollars (Decimal number, READ-ONLY)
Description: The actual dollar amount being risked on each trade. Formula: Account Balance × actual_risk_percent Example: $10,000 account × 3.0% = $300 risked per trade

4. POSITION SIZE CALCULATION SYSTEM
python
class RiskBasedPositionSizer:
    """Calculates position sizes based purely on risk parameters"""
    
    def calculate_position_size(self, account_balance: float, 
                              global_risk_percent: float,
                              risk_adjustment_multiplier: float, 
                              stop_loss_pips: int,
                              symbol: str) -> dict:
        """Calculate position size based on risk parameters only"""
        
        # Step 1: Calculate actual risk percentage
        raw_risk_percent = global_risk_percent * risk_adjustment_multiplier
        actual_risk_percent = min(raw_risk_percent, 3.5)  # Hard cap at 3.5%
        
        # Step 2: Calculate dollar risk amount
        risk_amount_dollars = account_balance * (actual_risk_percent / 100)
        
        # Step 3: Get pip value for the symbol
        pip_value = self.get_pip_value(symbol, account_balance)
        
        # Step 4: Calculate lot size
        if stop_loss_pips > 0 and pip_value > 0:
            calculated_lot_size = risk_amount_dollars / (stop_loss_pips * pip_value)
        else:
            calculated_lot_size = 0.0
        
        # Step 5: Apply broker constraints
        final_lot_size = self.apply_broker_constraints(calculated_lot_size, symbol)
        
        # Step 6: Recalculate actual risk with final lot size
        final_risk_dollars = final_lot_size * stop_loss_pips * pip_value
        final_risk_percent = (final_risk_dollars / account_balance) * 100
        
        return {
            "calculated_lot_size": final_lot_size,
            "actual_risk_percent": final_risk_percent,
            "risk_amount_dollars": final_risk_dollars,
            "pip_value": pip_value,
            "broker_min_lot": self.get_broker_min_lot(symbol),
            "broker_max_lot": self.get_broker_max_lot(symbol),
            "broker_lot_step": self.get_broker_lot_step(symbol),
            "calculation_valid": final_lot_size > 0,
            "risk_capped": raw_risk_percent > 3.5
        }
5. REENTRY RISK ADJUSTMENTS
reentry_risk_method (Text choice, default: "MAINTAIN_ORIGINAL")
Description: How to calculate risk for reentry trades:

"MAINTAIN_ORIGINAL" = Keep the same dollar risk as the original trade
"MAINTAIN_PERCENT" = Keep the same percentage risk (recalculated on current balance)
"REDUCE_PROGRESSIVE" = Reduce risk with each reentry level
"CHAIN_RISK_BUDGET" = Allocate total risk across the entire chain
reentry_risk_reduction (Decimal number, default: 0.8)
Description: If using progressive reduction, multiply risk by this amount for each reentry level. Example: 0.8 means each reentry uses 80% of the previous risk level Range: 0.1 to 1.0

chain_total_risk_percent (Decimal number, default: 5.0)
Description: If using chain risk budget, the total percentage of account that can be risked across all trades in one reentry chain. Example: 5.0% means the original trade + all reentries combined cannot risk more than 5% of account Range: 3.5% to 10.0%

max_reentry_risk_percent (Decimal number, default: 2.0)
Description: Maximum risk percentage allowed for any individual reentry trade. Purpose: Prevents reentries from becoming too large even if calculations suggest higher risk Range: 0.5% to 3.5%

6. UPDATED PARAMETER SET STRUCTURE
python
@dataclass
class RiskBasedParameterSet:
    # REQUIRED RISK PARAMETERS
    parameter_set_id: int
    name: str
    global_risk_percent: float          # REQUIRED: 0.1 to 3.5
    risk_adjustment_multiplier: float = 1.0  # 0.1 to 1.17
    
    # TRADING PARAMETERS
    stop_loss_pips: int                 # REQUIRED
    take_profit_pips: int               # REQUIRED
    entry_order_type: str               # REQUIRED
    
    # CALCULATED VALUES (READ-ONLY)
    calculated_lot_size: float = 0.0
    actual_risk_percent: float = 0.0
    risk_amount_dollars: float = 0.0
    
    # REENTRY RISK SETTINGS
    reentry_risk_method: str = "MAINTAIN_ORIGINAL"
    reentry_risk_reduction: float = 0.8
    chain_total_risk_percent: float = 5.0
    max_reentry_risk_percent: float = 2.0
    
    # ... (all other parameters remain the same)
7. USER INTERFACE CHANGES
Risk Configuration Panel
python
class RiskConfigurationUI:
    """UI focused entirely on risk management"""
    
    def create_risk_panel(self):
        """Create risk-focused parameter interface"""
        
        panel = QGroupBox("Risk Management (Position sizes calculated automatically)")
        layout = QFormLayout(panel)
        
        # Global risk setting (prominent display)
        self.global_risk_label = QLabel("Global Account Risk Per Trade:")
        self.global_risk_label.setStyleSheet("font-weight: bold; color: red;")
        
        self.global_risk_spin = QDoubleSpinBox()
        self.global_risk_spin.setRange(0.1, 3.5)
        self.global_risk_spin.setSingleStep(0.1)
        self.global_risk_spin.setSuffix("%")
        self.global_risk_spin.setDecimals(1)
        self.global_risk_spin.setValue(3.0)
        self.global_risk_spin.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        layout.addRow(self.global_risk_label, self.global_risk_spin)
        
        # Risk adjustment for this parameter set
        self.risk_adj_spin = QDoubleSpinBox()
        self.risk_adj_spin.setRange(0.1, 1.17)  # Max 1.17 to prevent exceeding 3.5% cap
        self.risk_adj_spin.setSingleStep(0.1)
        self.risk_adj_spin.setDecimals(2)
        self.risk_adj_spin.setValue(1.0)
        self.risk_adj_spin.valueChanged.connect(self.update_risk_display)
        
        layout.addRow("Risk Adjustment Multiplier:", self.risk_adj_spin)
        
        # Calculated risk display (read-only)
        self.actual_risk_display = QLabel("3.0%")
        self.actual_risk_display.setStyleSheet("font-weight: bold; color: blue;")
        layout.addRow("Actual Risk for This Set:", self.actual_risk_display)
        
        # Risk amount in dollars (read-only, updated from account balance)
        self.risk_dollars_display = QLabel("$300.00")
        self.risk_dollars_display.setStyleSheet("color: blue;")
        layout.addRow("Risk Amount (at current balance):", self.risk_dollars_display)
        
        # Position size display (read-only)
        self.position_size_display = QLabel("Will be calculated per trade")
        self.position_size_display.setStyleSheet("color: gray; font-style: italic;")
        layout.addRow("Position Size:", self.position_size_display)
        
        # Warning labels
        warning_label = QLabel("⚠️ Position sizes are automatically calculated based on risk settings and stop loss distance")
        warning_label.setStyleSheet("color: orange; font-size: 10px;")
        warning_label.setWordWrap(True)
        layout.addRow(warning_label)
        
        return panel
8. EXAMPLE RISK CALCULATIONS
Example 1: Conservative Setup
python
# Account Balance: $10,000
# Global Risk: 2.0%
# Risk Adjustment: 0.8 (conservative)
# Stop Loss: 50 pips

actual_risk_percent = 2.0% × 0.8 = 1.6%
risk_amount_dollars = $10,000 × 1.6% = $160
# If EURUSD pip value = $1 per 0.01 lot:
lot_size = $160 ÷ (50 pips × $1) = 3.2 × 0.01 = 0.032 lots
Example 2: Aggressive Setup
python
# Account Balance: $10,000  
# Global Risk: 3.0%
# Risk Adjustment: 1.15 (aggressive)
# Stop Loss: 30 pips

raw_risk = 3.0% × 1.15 = 3.45%
actual_risk_percent = 3.45% (within 3.5% cap)
risk_amount_dollars = $10,000 × 3.45% = $345
lot_size = $345 ÷ (30 pips × $1) = 11.5 × 0.01 = 0.115 lots
Example 3: Capped Risk
python
# Account Balance: $10,000
# Global Risk: 3.5%  
# Risk Adjustment: 1.2 (would exceed cap)
# Stop Loss: 40 pips

raw_risk = 3.5% × 1.2 = 4.2%
actual_risk_percent = 3.5% (CAPPED at maximum)
risk_amount_dollars = $10,000 × 3.5% = $350
lot_size = $350 ÷ (40 pips × $1) = 8.75 × 0.01 = 0.0875 lots
This system forces users to think in terms of risk rather than position size, preventing dangerous oversizing while maintaining flexibility through risk adjustment multipliers. The 3.5% hard cap ensures no single trade can cause catastrophic damage to the account.




Risk is adjusted based on of the same variables that create the matrix for example if the outcome is a four, the default should be to reduce risk with every reentry, but the time lapse from open to close can override that on market that is in breakout needs to be taken advantage of when the opportunity presents itself. Our definition of breakout is based mainly on if not solely on the time elapsed between the open and the clothes of the trade price that rises 20 pips in 30 minutes compared to price that rises 20 pips and three hours that difference in time is a big part of how we judge the strength of the move and when we get to a point that we have an extremely fast moving market and we’ll have to figure out you know the actual details but there are certain time conditions that would warrant not reducing risk at the reentry, but we do want to have the default be to reduce risk on reentry 80% on the first reentry and 50% on the second when the calculation is not a whole number the system should round down not up. As far as for the amount that can be wrist within a reentry chain that’s going to be determined by a separate global variable, which is gonna be max loss in a reentry chain if the original trade is profitable of four or five or six the entire risk of the trade of the reentry chain depends on the subsequent entries the original trade has already been profitable. We do want to calculate the amount of lots based on the risk and account value after every trade, it’s possible that a reentry trade may have a lower overall account percentage risk, but hold a larger position respective to lots if the original trade gain was great enough to allow the lower percentage risk of account value and absolute terms to be greater thanthe original trade. Does that make sense?

Edit
Dynamic Risk-Based Reentry System
Yes, that makes perfect sense! You're creating a sophisticated system where risk adjustments are determined by the matrix variables AND market conditions. Here's the complete structure:

1. MATRIX-DRIVEN RISK ADJUSTMENT SYSTEM
Core Risk Adjustment Variables
python
class MatrixRiskAdjustment:
    """Risk adjustments based on outcome + time + breakout conditions"""
    
    def __init__(self):
        # Default risk reduction by generation
        self.default_risk_reduction = {
            1: 0.8,  # First reentry: 80% of original risk
            2: 0.5,  # Second reentry: 50% of original risk  
            3: 0.3   # Third reentry: 30% of original risk
        }
        
        # Breakout time thresholds (pips achieved in time period)
        self.breakout_definitions = {
            "FLASH_BREAKOUT": {"pips": 20, "time_minutes": 5},    # 20 pips in 5 min
            "FAST_BREAKOUT": {"pips": 20, "time_minutes": 15},   # 20 pips in 15 min
            "NORMAL_BREAKOUT": {"pips": 20, "time_minutes": 30}, # 20 pips in 30 min
            "SLOW_MOVE": {"pips": 20, "time_minutes": 180}       # 20 pips in 3 hours
        }
Matrix-Based Risk Decision Logic
python
def calculate_reentry_risk_adjustment(self, 
                                    outcome: int,
                                    time_category: str, 
                                    original_pips_gained: float,
                                    time_elapsed_minutes: int,
                                    reentry_generation: int) -> dict:
    """Calculate risk adjustment based on matrix variables"""
    
    # Step 1: Determine breakout speed
    breakout_speed = self._classify_breakout_speed(original_pips_gained, time_elapsed_minutes)
    
    # Step 2: Apply outcome-based rules
    base_risk_adjustment = self._get_outcome_risk_adjustment(outcome, reentry_generation)
    
    # Step 3: Apply time/breakout overrides
    final_risk_adjustment = self._apply_breakout_overrides(
        base_risk_adjustment, breakout_speed, outcome, reentry_generation
    )
    
    return {
        "risk_multiplier": final_risk_adjustment,
        "breakout_classification": breakout_speed,
        "base_adjustment": base_risk_adjustment,
        "override_applied": final_risk_adjustment != base_risk_adjustment,
        "reasoning": self._get_risk_reasoning(outcome, breakout_speed, reentry_generation)
    }

def _get_outcome_risk_adjustment(self, outcome: int, generation: int) -> float:
    """Default risk adjustments by outcome and generation"""
    
    # Outcome 4, 5, 6 (profitable) - default is to reduce risk
    if outcome in [4, 5, 6]:
        return self.default_risk_reduction.get(generation, 0.2)
    
    # Outcome 1, 2 (losses) - more conservative reduction
    elif outcome in [1, 2]:
        return self.default_risk_reduction.get(generation, 0.2) * 0.7  # Even more conservative
    
    # Outcome 3 (breakeven) - moderate reduction
    else:
        return self.default_risk_reduction.get(generation, 0.2) * 0.9

def _apply_breakout_overrides(self, base_adjustment: float, breakout_speed: str, 
                            outcome: int, generation: int) -> float:
    """Override default risk reduction for strong breakouts"""
    
    # Only override for profitable outcomes (4, 5, 6)
    if outcome not in [4, 5, 6]:
        return base_adjustment
    
    # Strong breakouts override risk reduction
    if breakout_speed == "FLASH_BREAKOUT":
        # Flash breakouts: maintain higher risk for momentum
        if generation == 1:
            return 1.0  # Full risk on first reentry
        elif generation == 2:
            return 0.8  # Still aggressive on second
        else:
            return 0.5  # Conservative on third
    
    elif breakout_speed == "FAST_BREAKOUT":
        # Fast breakouts: moderate override
        if generation == 1:
            return 0.9  # Slightly reduce from full risk
        else:
            return max(base_adjustment, 0.6)  # Don't go below 60%
    
    elif breakout_speed == "NORMAL_BREAKOUT":
        # Normal speed: small override
        return max(base_adjustment, 0.7)  # Don't go below 70%
    
    # Slow moves: use default reduction
    return base_adjustment
2. REENTRY CHAIN RISK MANAGEMENT
Chain Risk Budget System
python
class ReentryChainRiskManager:
    """Manages total risk across an entire reentry chain"""
    
    def __init__(self):
        # Global chain risk limits
        self.max_chain_loss_percent = 8.0  # Maximum % of account that can be lost in one chain
        self.profitable_original_chain_budget = 15.0  # Higher budget when original was profitable
        
    def calculate_chain_risk_budget(self, original_trade_result: dict, 
                                   current_account_balance: float) -> dict:
        """Calculate available risk budget for the chain"""
        
        original_outcome = original_trade_result["outcome"]
        original_pnl = original_trade_result["pnl"]
        
        # If original trade was profitable (outcomes 4, 5, 6)
        if original_outcome in [4, 5, 6] and original_pnl > 0:
            # Use higher chain budget since we're "playing with house money"
            max_chain_loss = current_account_balance * (self.profitable_original_chain_budget / 100)
            reasoning = "Higher budget - original trade was profitable"
            
        else:
            # Standard conservative budget
            max_chain_loss = current_account_balance * (self.max_chain_loss_percent / 100)
            reasoning = "Standard budget - original trade not profitable"
        
        return {
            "max_chain_loss_dollars": max_chain_loss,
            "max_chain_loss_percent": max_chain_loss / current_account_balance * 100,
            "budget_type": "PROFITABLE_ORIGINAL" if original_outcome in [4, 5, 6] else "STANDARD",
            "reasoning": reasoning,
            "original_pnl": original_pnl
        }
3. DYNAMIC POSITION SIZING WITH ACCOUNT UPDATES
Real-Time Account-Based Sizing
python
class DynamicPositionSizer:
    """Calculates position size based on current account balance after each trade"""
    
    def calculate_reentry_position_size(self, 
                                      current_account_balance: float,
                                      base_risk_percent: float,
                                      risk_adjustment_multiplier: float,
                                      stop_loss_pips: int,
                                      symbol: str,
                                      chain_used_risk: float = 0.0) -> dict:
        """Calculate position size using current account balance"""
        
        # Step 1: Calculate raw risk percentage
        raw_risk_percent = base_risk_percent * risk_adjustment_multiplier
        
        # Step 2: Apply chain budget constraints
        remaining_chain_budget = self._get_remaining_chain_budget(
            current_account_balance, chain_used_risk
        )
        
        # Step 3: Cap risk at remaining budget
        capped_risk_percent = min(raw_risk_percent, remaining_chain_budget)
        
        # Step 4: Calculate position size
        risk_amount_dollars = current_account_balance * (capped_risk_percent / 100)
        pip_value = self.get_pip_value(symbol, current_account_balance)
        
        if stop_loss_pips > 0 and pip_value > 0:
            calculated_lots = risk_amount_dollars / (stop_loss_pips * pip_value)
            # ROUND DOWN as requested
            final_lots = math.floor(calculated_lots * 100) / 100  # Round down to 2 decimals
        else:
            final_lots = 0.0
        
        # Step 5: Apply broker constraints
        broker_adjusted_lots = self.apply_broker_constraints(final_lots, symbol)
        
        # Step 6: Calculate actual risk with final lot size
        actual_risk_dollars = broker_adjusted_lots * stop_loss_pips * pip_value
        actual_risk_percent = (actual_risk_dollars / current_account_balance) * 100
        
        return {
            "calculated_lots": broker_adjusted_lots,
            "actual_risk_percent": actual_risk_percent,
            "actual_risk_dollars": actual_risk_dollars,
            "raw_risk_percent": raw_risk_percent,
            "capped_by_chain_budget": capped_risk_percent < raw_risk_percent,
            "remaining_chain_budget_percent": remaining_chain_budget,
            "account_balance_used": current_account_balance,
            "rounded_down": broker_adjusted_lots < calculated_lots
        }
4. COMPLETE PARAMETER STRUCTURE
Updated Risk Parameters
python
# GLOBAL RISK SETTINGS (Account Level)
global_base_risk_percent: float = 3.0          # Base account risk per trade
max_chain_loss_percent: float = 8.0            # Max loss per chain (standard)
profitable_chain_budget_percent: float = 15.0  # Max loss per chain (when original profitable)

# MATRIX-DRIVEN RISK ADJUSTMENTS
default_reentry_risk_reduction: dict = {        # Default risk reduction by generation
    1: 0.8,  # 80% of original
    2: 0.5,  # 50% of original  
    3: 0.3   # 30% of original
}

# BREAKOUT OVERRIDES
breakout_risk_overrides: dict = {
    "FLASH_BREAKOUT": {     # 20+ pips in ≤5 minutes
        1: 1.0,             # Full risk on first reentry
        2: 0.8,             # 80% on second
        3: 0.5              # 50% on third
    },
    "FAST_BREAKOUT": {      # 20+ pips in ≤15 minutes  
        1: 0.9,             # 90% risk on first reentry
        2: 0.6,             # 60% on second and beyond
        3: 0.6
    },
    "NORMAL_BREAKOUT": {    # 20+ pips in ≤30 minutes
        1: 0.7,             # Don't go below 70%
        2: 0.7,
        3: 0.7
    }
}

# OUTCOME-BASED MODIFIERS
outcome_risk_modifiers: dict = {
    1: 0.7,  # Full SL - very conservative (70% of default reduction)
    2: 0.7,  # Partial loss - very conservative  
    3: 0.9,  # Breakeven - moderately conservative (90% of default)
    4: 1.0,  # Partial profit - use default reduction
    5: 1.0,  # Full TP - use default reduction
    6: 1.0   # Beyond TP - use default reduction
}
5. EXAMPLE CALCULATIONS
Example 1: Profitable Trade with Fast Breakout
python
# Original Trade: EURUSD, outcome 5 (full TP), gained 22 pips in 12 minutes
# Account after original: $10,500 (was $10,000, gained $500)
# First reentry: 40 pip SL

# Classification
breakout_speed = "FAST_BREAKOUT"  # 22 pips in 12 min
outcome = 5  # Full TP

# Risk calculation  
default_reduction = 0.8  # 80% for first reentry
outcome_modifier = 1.0   # No modifier for outcome 5
breakout_override = 0.9  # Fast breakout override
final_risk_multiplier = 0.9  # Override wins

# Position sizing
base_risk = 3.0%
adjusted_risk = 3.0% × 0.9 = 2.7%
risk_dollars = $10,500 × 2.7% = $283.50
lots = $283.50 ÷ (40 pips × $1) = 7.09 lots → 7.08 lots (rounded down)
Example 2: Chain Budget Constraint
python
# Original trade lost $300, first reentry lost $200
# Chain used risk so far: $500
# Account balance: $9,500
# Standard chain budget: $9,500 × 8% = $760
# Remaining budget: $760 - $500 = $260

# Second reentry calculation
base_risk = 3.0%  
risk_multiplier = 0.5  # Second reentry default
calculated_risk = 3.0% × 0.5 = 1.5%
calculated_dollars = $9,500 × 1.5% = $142.50

# Budget check: $142.50 < $260 remaining ✓ (within budget)
# Position size calculated normally
Example 3: Profitable Original - Higher Chain Budget
python
# Original trade: Outcome 6, profit $800
# Account balance: $10,800  
# Chain budget: $10,800 × 15% = $1,620 (higher budget for profitable original)

# This allows for more aggressive reentries since original was profitable
# and we're "playing with house money"
This system elegantly balances:

Default risk reduction for safety
Breakout momentum capture when markets are moving fast
Chain budget management to prevent catastrophic losses
Dynamic position sizing based on current account balance
Automatic rounding down for conservative position sizing
The key insight is that fast price movements (breakouts) override conservative defaults because they represent genuine momentum opportunities that should be capitalized on.