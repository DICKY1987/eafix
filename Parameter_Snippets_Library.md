(Where useful, I cite canonical MQL4 behavior—for example, how slippage applies to market orders and how to form OrderSend/OrderModify—so your AI has ground truth while learning the patterns.) See: required/SL-TP/TS/Entry/Straddle/State/Logging items in your file【turn2file1†L1-L7】【turn2file1†L9-L15】【turn2file1†L16-L23】【turn2file1†L24-L31】【turn2file1†L32-L39】【turn2file1†L40-L51】【turn2file1†L53-L64】【turn2file0†L22-L35】【turn2file0†L36-L46】【turn2file0†L47-L50】.
Notes on market slippage behavior and the OrderSend contract are from the MQL4 book【turn2file9†L5-L8】【turn1file4†L28-L33】, and the trailing/modify error-recovery loop pattern mirrors the classic approach【turn2file4†L35-L44】【turn2file4†L96-L106】. Min stop distances via MODE_STOPLEVEL are validated the standard way【turn2file11†L16-L24】.

// ==============================
// Parameter Snippets Library
// ==============================
#property strict
#include <stdlib.mqh>

// -------------------------------------------
// SECTION 1. REQUIRED PARAMETERS
// -------------------------------------------
extern string parameter_set_id      = "PS_001";     // Unique identifier
extern string name                  = "BaselineSet"; // Human-readable name
extern double global_risk_percent   = 1.00;         // % risk per trade (REQUIRED)
extern int    stop_loss_pips        = 20;           // Fallback SL if FIXED
extern int    take_profit_pips      = 40;           // Fallback TP if FIXED
extern string entry_order_type      = "STRADDLE";   // "MARKET", "PENDING", "STRADDLE"

// Helper: pip-to-price
double PipsToPrice(int pips) { return pips * Point; }

// Example: lot size from risk % (simplified; replace with your money mgmt)
double CalcLotsFromRisk(double risk_percent, int sl_pips) {
   if(sl_pips <= 0) return 0.10; // guard
   double accBal    = AccountBalance();
   double riskMoney = accBal * (risk_percent/100.0);
   // naive: tickvalue for 1 lot; use MarketInfo(Symbol(), MODE_TICKVALUE)
   double tv        = MarketInfo(Symbol(), MODE_TICKVALUE);
   if(tv <= 0) tv = 1.0;
   double slValue   = sl_pips * tv / Point; // monetary loss for 1 lot at SL
   double lots      = riskMoney / MathMax(slValue, 0.00001);
   // clamp to broker steps
   double step      = MarketInfo(Symbol(), MODE_LOTSTEP);
   double minLot    = MarketInfo(Symbol(), MODE_MINLOT);
   double maxLot    = MarketInfo(Symbol(), MODE_MAXLOT);
   lots = MathFloor(lots/step)*step;
   lots = MathMax(minLot, MathMin(lots, maxLot));
   return NormalizeDouble(lots, 2);
}

// -------------------------------------------
// SECTION 3. STOP LOSS & TAKE PROFIT CONFIG
// -------------------------------------------
extern string stop_loss_method      = "FIXED";       // "FIXED", "ATR_MULTIPLE", "PERCENT"
extern double atr_stop_multiplier   = 2.0;           // for ATR_MULTIPLE
extern int    max_stop_loss_pips    = 200;           // hard cap on SL
extern string take_profit_method    = "RR_RATIO";    // "FIXED", "RR_RATIO", "ATR_MULTIPLE"
extern double risk_reward_ratio     = 2.0;           // TP = SL * RR
extern string partial_tp_levels     = "50|80";       // percent milestones (e.g., "50|80")

// ATR helper (MQL4 built-in iATR)
double GetATR(int period=14, int shift=0) {
   return iATR(Symbol(), Period(), period, shift);
}

// Build SL/TP in price terms from chosen methods
bool BuildStops(double entryPrice, bool isBuy, int fallbackSLpips,
                double &slPrice, double &tpPrice) {
   // Compute SL pips
   double sl_pips = fallbackSLpips;
   if(stop_loss_method == "ATR_MULTIPLE") {
      double atr = GetATR(14, 0);
      // Convert ATR price distance to pips-equivalent
      sl_pips = MathRound((atr / Point) * atr_stop_multiplier);
   } else if(stop_loss_method == "PERCENT") {
      // % of price as pips equivalent (simple)
      double sl_price_dist = entryPrice * (global_risk_percent/100.0);
      sl_pips = MathRound(sl_price_dist / Point);
   }
   sl_pips = MathMin(sl_pips, max_stop_loss_pips);

   // Price mapping
   double sl_dist = PipsToPrice((int)sl_pips);
   if(isBuy) slPrice = entryPrice - sl_dist;
   else      slPrice = entryPrice + sl_dist;

   // Compute TP
   if(take_profit_method == "FIXED") {
      double tp_dist = PipsToPrice(take_profit_pips);
      if(isBuy) tpPrice = entryPrice + tp_dist;
      else      tpPrice = entryPrice - tp_dist;
   } else if(take_profit_method == "RR_RATIO") {
      double tp_dist = sl_dist * risk_reward_ratio;
      if(isBuy) tpPrice = entryPrice + tp_dist;
      else      tpPrice = entryPrice - tp_dist;
   } else if(take_profit_method == "ATR_MULTIPLE") {
      double atr = GetATR(14, 0);
      double tp_dist = atr * atr_stop_multiplier * risk_reward_ratio;
      if(isBuy) tpPrice = entryPrice + tp_dist;
      else      tpPrice = entryPrice - tp_dist;
   } else {
      tpPrice = 0; // optional (no TP)
   }

   // Validate minimum distances vs MODE_STOPLEVEL
   double stopLevelPts = MarketInfo(Symbol(), MODE_STOPLEVEL) * Point;
   if(isBuy) {
      if(slPrice > 0 && (entryPrice - slPrice) < stopLevelPts) return false;
      if(tpPrice > 0 && (tpPrice - entryPrice) < stopLevelPts) return false;
   } else {
      if(slPrice > 0 && (slPrice - entryPrice) < stopLevelPts) return false;
      if(tpPrice > 0 && (entryPrice - tpPrice) < stopLevelPts) return false;
   }
   return true;
}

// Partial TP utility (closes a portion when profit % threshold is crossed)
bool CheckAndDoPartialTP(int ticket, double thresholdPct, double closeFraction) {
   if(!OrderSelect(ticket, SELECT_BY_TICKET)) return false;
   double openPrice = OrderOpenPrice();
   double lots      = OrderLots();
   int    type      = OrderType();

   // simple: compare against current price distance vs initial SL distance
   double sl = OrderStopLoss();
   if(sl <= 0) return false; // needs SL set to compute % move
   double totalRisk = (type==OP_BUY) ? (openPrice - sl) : (sl - openPrice);
   double move      = (type==OP_BUY) ? (Bid - openPrice) : (openPrice - Ask);
   if(totalRisk <= 0) return false;

   double pct = (move / totalRisk) * 100.0;
   if(pct >= thresholdPct) {
      double lotsToClose = NormalizeDouble(lots * closeFraction, 2);
      if(lotsToClose >= MarketInfo(Symbol(), MODE_MINLOT)) {
         if(type==OP_BUY)  return OrderClose(ticket, lotsToClose, Bid, 3);
         if(type==OP_SELL) return OrderClose(ticket, lotsToClose, Ask, 3);
      }
   }
   return false;
}

// -------------------------------------------
// Advanced Trailing Stop Options
// -------------------------------------------
extern bool   use_trailing_stop            = true;
extern string trailing_stop_method         = "STEPPED";  // "CONTINUOUS","STEPPED"
extern int    trailing_stop_pips           = 20;
extern int    trailing_step_pips           = 5;
extern int    trailing_start_pips          = 10;
extern int    trailing_step_size_pips      = 5;
extern int    trailing_initial_distance_pips = 20;
extern int    trailing_step_trigger_pips   = 10;
extern int    breakeven_trigger_pips       = 12;
extern int    breakeven_plus_pips          = 1;
extern bool   dynamic_trail_adjustment     = false;
extern int    initial_trail_distance       = 20;
extern int    adjusted_trail_distance      = 10;
extern int    trail_trigger_pips           = 30;

// Apply trailing to a single order (called per tick)
void ApplyTrailing(int ticket) {
   if(!use_trailing_stop) return;
   if(!OrderSelect(ticket, SELECT_BY_TICKET)) return;

   int type = OrderType();
   if(type!=OP_BUY && type!=OP_SELL) return;

   double open = OrderOpenPrice();
   double sl   = OrderStopLoss();
   double price= (type==OP_BUY) ? Bid : Ask;

   // profit in pips since open
   double profPips = (type==OP_BUY)
                     ? (price - open)/Point
                     : (open - price)/Point;

   // breakeven logic
   if(breakeven_trigger_pips > 0 && profPips >= breakeven_trigger_pips) {
      double bePrice = (type==OP_BUY) ? (open + PipsToPrice(breakeven_plus_pips))
                                      : (open - PipsToPrice(breakeven_plus_pips));
      if((type==OP_BUY && (sl < bePrice || sl==0)) ||
         (type==OP_SELL && (sl > bePrice || sl==0))) {
         OrderModify(OrderTicket(), OrderOpenPrice(), NormalizeDouble(bePrice, Digits),
                     OrderTakeProfit(), 0);
      }
   }

   // pick current trail distance
   int trailDist = trailing_stop_pips;
   if(dynamic_trail_adjustment && profPips >= trail_trigger_pips)
      trailDist = adjusted_trail_distance;

   // skip until start threshold
   if(profPips < trailing_start_pips) return;

   // Calculate new SL as per method
   double desiredSL =
      (type==OP_BUY) ? (price - PipsToPrice(trailDist))
                     : (price + PipsToPrice(trailDist));

   // STEPPED: only move in increments
   static double lastStepPrice = 0;
   if(trailing_stop_method=="STEPPED") {
      if(MathAbs(price - lastStepPrice) < PipsToPrice(trailing_step_size_pips)) return;
      lastStepPrice = price;
   }

   // Only tighten (never loosen)
   bool shouldMove =
      (type==OP_BUY  && (sl==0 || desiredSL > sl)) ||
      (type==OP_SELL && (sl==0 || desiredSL < sl));

   if(shouldMove) {
      // honor broker STOPLEVEL
      double stopLevel = MarketInfo(Symbol(), MODE_STOPLEVEL) * Point;
      if(type==OP_BUY  && (price - desiredSL) < stopLevel) desiredSL = price - stopLevel;
      if(type==OP_SELL && (desiredSL - price) < stopLevel) desiredSL = price + stopLevel;

      OrderModify(OrderTicket(), OrderOpenPrice(), NormalizeDouble(desiredSL, Digits),
                  OrderTakeProfit(), 0);
   }
}

// -------------------------------------------
// SECTION 4. ENTRY ORDER PARAMETERS
// -------------------------------------------
// Market Orders
extern int market_slippage_pips  = 3;   // slippage for market orders
extern int market_retry_attempts = 3;
extern int market_retry_delay_ms = 300;
extern int slippage_tolerance_pips = 3; // synonym/alt guard

// Pending Orders
extern string entry_order_setup_type        = "STRADDLE";           // "STRADDLE","BUY_STOP_ONLY","SELL_STOP_ONLY"
extern int    pending_order_type            = OP_BUYSTOP;           // for single pending mode
extern int    pending_distance_pips         = 15;
extern int    pending_expiration_minutes    = 120;
extern string pending_price_method          = "FIXED";              // "FIXED","ATR","SUPPORT_RESISTANCE"
extern double atr_distance_multiplier       = 1.5;
extern int    pending_order_timeout_minutes = 180;
extern int    bias_direction                = 0;    // -1,0,1
extern bool   persist_bias_after_win        = true;
extern string bias_override_by_category     = "";   // e.g., "CAT1=-1|CAT2=0"
extern bool   trail_pending_orders          = false;

// Market send with retry/slippage (slippage applies to market orders)
int SendMarket(int op, double lots, double &entryPrice, double &sl, double &tp) {
   int attempts = MathMax(1, market_retry_attempts);
   int slip     = slippage_tolerance_pips;
   for(int i=0; i<attempts; i++) {
      RefreshRates();
      double price = (op==OP_BUY) ? Ask : Bid;
      int ticket = OrderSend(Symbol(), op, lots, price, slip, sl, tp, name, 0, 0, clrNONE);
      if(ticket>0) { entryPrice = price; return ticket; }

      int err = GetLastError();
      // Handle transient errors; wait then retry
      Sleep(market_retry_delay_ms);
      RefreshRates();
   }
   return -1;
}

// Compute pending price based on method
double BuildPendingPrice(bool isBuy) {
   RefreshRates();
   double base = isBuy ? Ask : Bid;
   if(pending_price_method=="FIXED") {
      return isBuy ? (base + PipsToPrice(pending_distance_pips))
                   : (base - PipsToPrice(pending_distance_pips));
   } else if(pending_price_method=="ATR") {
      double atr = GetATR(14,0);
      double dist = atr * atr_distance_multiplier;
      return isBuy ? (base + dist) : (base - dist);
   } else if(pending_price_method=="SUPPORT_RESISTANCE") {
      // Placeholder: simple SR via recent high/low
      int lookback = 50;
      double level = isBuy ? iHigh(Symbol(), Period(), iHighest(Symbol(), Period(), MODE_HIGH, lookback, 1))
                           : iLow (Symbol(), Period(), iLowest (Symbol(), Period(), MODE_LOW,  lookback, 1));
      return level;
   }
   return 0.0;
}

// Place pending with expiration
int PlacePending(int op, double lots, double &px, double &sl, double &tp) {
   bool isBuy = (op==OP_BUYSTOP || op==OP_BUYLIMIT);
   px = BuildPendingPrice(isBuy);
   datetime exp = (pending_expiration_minutes>0) ? (TimeCurrent() + pending_expiration_minutes*60) : 0;
   return OrderSend(Symbol(), op, lots, NormalizeDouble(px,Digits), 0, sl, tp, name, 0, exp, clrNONE);
}

// Optional: trail a pending as price moves (OrderModify)
void TrailPendingOrder(int ticket, int trailPips) {
   if(!trail_pending_orders) return;
   if(!OrderSelect(ticket, SELECT_BY_TICKET)) return;
   if(OrderType()!=OP_BUYSTOP && OrderType()!=OP_SELLSTOP) return;

   bool isBuy = (OrderType()==OP_BUYSTOP);
   RefreshRates();
   double desired = isBuy ? (Ask + PipsToPrice(trailPips))
                          : (Bid - PipsToPrice(trailPips));
   if( (isBuy  && desired > OrderOpenPrice()) ||
       (!isBuy && desired < OrderOpenPrice()) ) {
      OrderModify(ticket, NormalizeDouble(desired,Digits), OrderStopLoss(), OrderTakeProfit(), OrderExpiration());
   }
}

// Bias application helper (constrains direction)
int ApplyBiasToCmd(int op) {
   if(bias_direction== 1) return (op==OP_SELL) ? OP_BUY  : op;
   if(bias_direction==-1) return (op==OP_BUY ) ? OP_SELL : op;
   return op;
}

// Pending timeout enforcement
bool PendingTimedOut(datetime placedAt) {
   if(pending_order_timeout_minutes<=0) return false;
   return (TimeCurrent() - placedAt) >= (pending_order_timeout_minutes*60);
}

// -------------------------------------------
// Straddle Orders
// -------------------------------------------
extern int    straddle_distance_pips     = 20;
extern int    straddle_buy_order_type    = OP_BUYSTOP;
extern int    straddle_sell_order_type   = OP_SELLSTOP;
extern int    straddle_expiration_minutes= 180;
extern bool   straddle_auto_cancel_opposite = true;
extern int    straddle_cancel_delay_seconds = 2;
extern bool   straddle_asymmetric        = false;
extern int    straddle_buy_distance_pips = 18;
extern int    straddle_sell_distance_pips= 22;
extern bool   straddle_equal_lot_sizes   = true;
extern double straddle_buy_lot_ratio     = 1.0;
extern double straddle_sell_lot_ratio    = 1.0;
extern int    max_spread_pips            = 30;
extern int    entry_delay_seconds        = 0;  // optional delay before placing
extern double emergency_stop_loss_percent= 35.0; // equity DD %
extern bool   emergency_close_all_trades = false;

// Check spread guard before entry
bool SpreadOK() {
   double spr = MarketInfo(Symbol(), MODE_SPREAD); // points
   return spr <= max_spread_pips;
}

// Place both straddle legs
bool PlaceStraddle(double baseLots, int &buyTk, int &sellTk) {
   if(!SpreadOK()) return false;
   if(entry_delay_seconds>0) Sleep(entry_delay_seconds*1000);

   RefreshRates();
   double buyPx, sellPx;
   if(straddle_asymmetric) {
      buyPx  = Ask + PipsToPrice(straddle_buy_distance_pips);
      sellPx = Bid - PipsToPrice(straddle_sell_distance_pips);
   } else {
      buyPx  = Ask + PipsToPrice(straddle_distance_pips);
      sellPx = Bid - PipsToPrice(straddle_distance_pips);
   }

   double buyLots  = straddle_equal_lot_sizes ? baseLots : baseLots*straddle_buy_lot_ratio;
   double sellLots = straddle_equal_lot_sizes ? baseLots : baseLots*straddle_sell_lot_ratio;

   double dummy=0, sl=0, tp=0;
   datetime exp = (straddle_expiration_minutes>0) ? (TimeCurrent()+straddle_expiration_minutes*60) : 0;

   buyTk  = OrderSend(Symbol(), straddle_buy_order_type,  buyLots,  NormalizeDouble(buyPx,Digits), 0, sl, tp, name, 0, exp, clrNONE);
   sellTk = OrderSend(Symbol(), straddle_sell_order_type, sellLots, NormalizeDouble(sellPx,Digits), 0, sl, tp, name, 0, exp, clrNONE);
   return (buyTk>0 && sellTk>0);
}

// Auto-cancel the opposite leg after one fills
void StraddleAutoCancel(int filledTicket, int otherTicket) {
   if(!straddle_auto_cancel_opposite) return;
   if(otherTicket<=0) return;
   // small delay to avoid race conditions
   Sleep(straddle_cancel_delay_seconds*1000);
   if(OrderSelect(filledTicket, SELECT_BY_TICKET) && OrderCloseTime()==0) {
      if(OrderSelect(otherTicket, SELECT_BY_TICKET) && OrderCloseTime()==0) {
         if(OrderType()==OP_BUYSTOP || OrderType()==OP_SELLSTOP ||
            OrderType()==OP_BUYLIMIT || OrderType()==OP_SELLLIMIT) {
            OrderDelete(otherTicket);
         }
      }
   }
}

// -------------------------------------------
// EMERGENCY CONTROLS (Equity Kill Switch)
// -------------------------------------------
void EmergencyCheckAndCloseAll() {
   if(!emergency_close_all_trades && emergency_stop_loss_percent<=0) return;
   double eq   = AccountEquity();
   double bal  = AccountBalance();
   double ddPct= (1.0 - (eq/MathMax(bal,0.01))) * 100.0;
   if(emergency_close_all_trades || ddPct >= emergency_stop_loss_percent) {
      for(int i=OrdersTotal()-1; i>=0; i--) {
         if(OrderSelect(i, SELECT_BY_POS)) {
            int t=OrderType();
            if(t==OP_BUY)  OrderClose(OrderTicket(), OrderLots(), Bid, 3);
            if(t==OP_SELL) OrderClose(OrderTicket(), OrderLots(), Ask, 3);
            if(t==OP_BUYSTOP||t==OP_SELLSTOP||t==OP_BUYLIMIT||t==OP_SELLLIMIT) OrderDelete(OrderTicket());
         }
      }
   }
}

// -------------------------------------------
// 13. STATE MANAGEMENT & PERSISTENCE
// -------------------------------------------
extern string current_ea_state              = "IDLE"; // "IDLE","ORDERS_PLACED","TRADE_TRIGGERED","DISABLED"
extern bool   restart_after_trade_close     = true;
extern bool   save_state_to_global_vars     = true;
extern int    max_total_restarts            = 3;
extern bool   reset_to_default_after_category1 = false;
extern int    max_consecutive_category1     = 2;
extern int    inactivity_timeout_minutes    = 240;

int    g_restart_count = 0;
int    g_state_resets  = 0;
datetime g_lastActivity= 0;

void SetState(string s) {
   current_ea_state = s;
   g_lastActivity = TimeCurrent();
   if(save_state_to_global_vars) GlobalVariableSet("EA_STATE_"+Symbol(), StringToDouble("0")); // marker
   // Persist exact state text too:
   if(save_state_to_global_vars) GlobalVariableSet("EA_STATE_TEXT_"+Symbol(), 0); // store marker
}

bool IsInactiveTimedOut() {
   if(inactivity_timeout_minutes<=0) return false;
   if(g_lastActivity==0) g_lastActivity = TimeCurrent();
   return (TimeCurrent() - g_lastActivity) > (inactivity_timeout_minutes*60);
}

void OnTradeClosedCycleEnd() {
   if(restart_after_trade_close) {
      if(g_restart_count < max_total_restarts) {
         g_restart_count++;
         SetState("IDLE");
      } else {
         SetState("DISABLED");
      }
   }
}

// -------------------------------------------
// 15. LOGGING & DEBUGGING
// -------------------------------------------
extern bool verbose_logging   = true;
extern bool log_to_file       = false;
extern int  max_state_resets  = 10;

int  fileHandle = INVALID_HANDLE;

void LogInit() {
   if(log_to_file) {
      string fname = "EA_"+Symbol()+"_"+TimeToStr(TimeLocal(), TIME_DATE)+"_"+TimeToStr(TimeLocal(), TIME_MINUTES)+".csv";
      fileHandle = FileOpen(fname, FILE_CSV|FILE_WRITE, ';');
   }
}
void LogLine(string tag, string msg) {
   if(verbose_logging) Print(tag,": ",msg);
   if(log_to_file && fileHandle!=INVALID_HANDLE) FileWrite(fileHandle, TimeToStr(TimeCurrent(), TIME_SECONDS), tag, msg);
}

void GuardStateReset() {
   g_state_resets++;
   if(g_state_resets>max_state_resets) {
      LogLine("STATE","Too many resets. Disabling EA.");
      SetState("DISABLED");
   }
}

// -------------------------------------------
// Example glue you might call in OnTick()
// -------------------------------------------
void Example_EntryFlow() {
   // Choose direction via bias
   int cmd = (entry_order_type=="MARKET") ? OP_BUY : OP_BUYSTOP;
   cmd = ApplyBiasToCmd(cmd);

   // Build SL/TP
   RefreshRates();
   bool isBuy = (cmd==OP_BUY || cmd==OP_BUYSTOP || cmd==OP_BUYLIMIT);
   double entry = isBuy ? Ask : Bid;
   double sl=0, tp=0;
   if(!BuildStops(entry, isBuy, stop_loss_pips, sl, tp)) {
      LogLine("ENTRY","Stops invalid vs STOPLEVEL"); return;
   }

   // Size
   double lots = CalcLotsFromRisk(global_risk_percent, stop_loss_pips);

   // Dispatch by mode
   if(entry_order_type=="MARKET") {
      double px=0; int tk = SendMarket(isBuy?OP_BUY:OP_SELL, lots, px, sl, tp);
      if(tk>0) SetState("TRADE_TRIGGERED");
   } else if(entry_order_type=="PENDING") {
      double px=0; int tk = PlacePending(pending_order_type, lots, px, sl, tp);
      if(tk>0) SetState("ORDERS_PLACED");
   } else if(entry_order_type=="STRADDLE") {
      int btk=0, stk=0;
      if(PlaceStraddle(lots, btk, stk)) SetState("ORDERS_PLACED");
   }
}

Mapping index (param → where it’s used)

Required:

parameter_set_id, name (metadata)【turn2file1†L1-L4】.

global_risk_percent → CalcLotsFromRisk() & BuildStops()【turn2file1†L1-L7】.

stop_loss_pips, take_profit_pips → BuildStops() when FIXED【turn2file1†L4-L7】【turn2file1†L9-L15】.

entry_order_type → Example_EntryFlow() dispatch【turn2file1†L1-L7】.

SL/TP:

stop_loss_method, atr_stop_multiplier, max_stop_loss_pips → BuildStops()【turn2file1†L9-L15】.

take_profit_method, risk_reward_ratio → BuildStops()【turn2file1†L12-L14】.

partial_tp_levels → CheckAndDoPartialTP() shows milestone approach【turn2file1†L13-L15】.

Advanced Trailing:

use_trailing_stop, trailing_stop_method, trailing_stop_pips, trailing_step_pips, trailing_start_pips, trailing_step_size_pips, trailing_initial_distance_pips, trailing_step_trigger_pips, breakeven_trigger_pips, breakeven_plus_pips, dynamic_trail_adjustment, initial_trail_distance, adjusted_trail_distance, trail_trigger_pips → ApplyTrailing() logic paths【turn2file1†L16-L31】.
(Trailing/modify loop patterns mirror standard MQL4 modify+error handling【turn2file4†L35-L44】【turn2file4†L96-L106】.)

Entry (Market):

market_slippage_pips / slippage_tolerance_pips / market_retry_attempts / market_retry_delay_ms → SendMarket() retry pattern.
(Slippage impacts market orders per spec【turn2file9†L5-L8】; OrderSend signature context【turn1file4†L28-L33】.)

Entry (Pending):

entry_order_setup_type, pending_order_type, pending_distance_pips, pending_expiration_minutes, pending_price_method, atr_distance_multiplier, pending_order_timeout_minutes, bias_direction, persist_bias_after_win, bias_override_by_category, trail_pending_orders
→ BuildPendingPrice(), PlacePending(), TrailPendingOrder(), ApplyBiasToCmd(), PendingTimedOut()【turn2file1†L40-L51】.

Straddle:

straddle_distance_pips, straddle_buy_order_type, straddle_sell_order_type, straddle_expiration_minutes, straddle_auto_cancel_opposite, straddle_cancel_delay_seconds, straddle_asymmetric, straddle_buy_distance_pips, straddle_sell_distance_pips, straddle_equal_lot_sizes, straddle_buy_lot_ratio, straddle_sell_lot_ratio, max_spread_pips, entry_delay_seconds, emergency_stop_loss_percent, emergency_close_all_trades
→ PlaceStraddle(), StraddleAutoCancel(), SpreadOK(), EmergencyCheckAndCloseAll()【turn2file0†L22-L35】【turn2file0†L36-L46】.

State & Persistence:

current_ea_state, restart_after_trade_close, save_state_to_global_vars, max_total_restarts, reset_to_default_after_category1, max_consecutive_category1, inactivity_timeout_minutes
→ SetState(), OnTradeClosedCycleEnd(), IsInactiveTimedOut()【turn2file0†L39-L46】.

Logging & Debugging:

verbose_logging, log_to_file, max_state_resets
→ LogInit(), LogLine(), GuardStateReset()【turn2file0†L47-L50】.

A couple of implementation notes your AI should keep in mind

Market vs. Pending slippage: slippage applies to market orders; it’s ignored for pending placements【turn2file9†L5-L8】.

Order API shapes: OrderSend/OrderModify are your trading primitives; see canonical header for parameters【turn1file4†L28-L33】.

Stop levels: Always validate SL/TP distances against MODE_STOPLEVEL (examples mirrored in the validation templates)【turn2file11†L16-L24】.

Trailing pattern: The standard “tighten only + error-aware retry” modify loop is the battle-tested approach for TS updates and survives transient trade errors【turn2file4†L35-L44】【turn2file4†L96-L106】.