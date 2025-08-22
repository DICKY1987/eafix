#property strict
#property copyright "HUEY_P Project"
#property link      "local"
#property version   "1.00"
#property description "Three-tier communication EA (Autonomous, CSV, DLL) + recorder and circuit breaker"

#include <stdlib.mqh>

// ==========================
// ===== User Parameters =====
// ==========================

// --- Identity / scope
extern string   TargetCurrencyPair              = "";       // leave blank to accept current chart symbol only
extern int      Magic                           = 88008;

// --- Autonomous mode (Tier 1)
extern bool     AutonomousMode                  = false;
extern bool     AutoPlaceStraddle               = false;
extern double   StraddleDistancePips            = 20.0;
extern double   StraddleLotSize                 = 0.01;
extern int      StraddleExpiryMinutes           = 60;

// --- CSV signals (Tier 2)
extern bool     EnableCSVSignals                = true;
extern string   CSVSignalFile                   = "signals.csv";     // MQL4/Files/
extern string   CSVResponseFile                 = "responses.csv";   // MQL4/Files/
extern int      CSVCheckIntervalSeconds         = 2;
extern int      SignalExecutionToleranceSeconds = 5;

// --- DLL/Socket signals (Tier 3)
extern bool     EnableDLLSignals                = false;
extern int      ListenPort                      = 19999;             // requires vetted DLL + 'Allow DLL imports' option

// --- Risk / Circuit breaker
extern bool     EnableCircuitBreaker            = true;
extern double   MaxEquityDrawdownPct            = 20.0;  // trip if equity falls this % from peak
extern bool     ClosePositionsOnTrip            = false; // if true, closes all positions for scope (symbol+magic)

// --- Python heartbeat (optional, file-based keepalive from Python controller)
extern bool     EnableHeartbeat                 = false;
extern string   HeartbeatFile                   = "python_heartbeat.txt"; // MQL4/Files/
extern int      PythonHeartbeatTimeoutSec       = 60;

// --- Order safety
extern int      SlippagePoints                  = 5;
extern int      OrderRetryAttempts              = 2;
extern int      OrderRetryDelayMs               = 200;

// --- Logging
extern bool     EnableCommentHUD                = true;

// ==========================
// ====== DLL Imports  ======
// ==========================
// NOTE: This import will be resolved at call time. Keep EnableDLLSignals=false if you don't have the DLL.
#import "MQL4_DLL_SocketBridge.dll"
   int   StartServer(int port, int hWnd, int messageId);
   void  StopServer();
   int   GetLastMessage(uchar &buffer[], int maxSize);
   int   GetCommunicationStatus(int socketId);
   bool  SocketIsConnected(int socketId);
   string GetLastSocketError();
   bool  SocketSendHeartbeat(int socketId);
#import

// ==========================
// ====== Global State  =====
// ==========================

#define CUSTOM_EVENT_ID (CHARTEVENT_CUSTOM+1)

bool     g_circuitTripped      = false;
double   g_equityPeak          = 0.0;
datetime g_lastCSVCheck        = 0;
bool     g_dllSignalProcessing = false;

int      g_socketId            = -1;     // managed by DLL if available

// For duplicate-signal suppression (CSV)
string   g_processedIds[1024];
int      g_processedCount = 0;

// ==========================
// ===== Data Structures ====
// ==========================

struct CSVSignal
{
   datetime executionTime;
   string   symbol;
   int      orderType;     // 0=OP_BUY,1=OP_SELL,2=OP_BUYLIMIT,3=OP_SELLLIMIT,4=OP_BUYSTOP,5=OP_SELLSTOP
   double   lot;
   double   sl;
   double   tp;
   string   comment;
};

// ==========================
// ======= Utilities ========
// ==========================

string ScopeSymbol()
{
   string s = (TargetCurrencyPair=="" ? Symbol() : TargetCurrencyPair);
   return s;
}

double PipValueInPoints()
{
   // For 5-digit brokers, pip = 10 * Point; for 3-digit JPY pairs, similar
   if(Digits==5 || Digits==3) return 10*Point;
   return Point;
}

double NormalizeLot(double lots)
{
   double minLot   = MarketInfo(ScopeSymbol(), MODE_MINLOT);
   double maxLot   = MarketInfo(ScopeSymbol(), MODE_MAXLOT);
   double lotStep  = MarketInfo(ScopeSymbol(), MODE_LOTSTEP);
   lots = MathMax(minLot, MathMin(lots, maxLot));
   int steps = (int)MathFloor((lots - minLot + 0.5*lotStep)/lotStep);
   double normalized = minLot + steps*lotStep;
   return MathMax(minLot, MathMin(normalized, maxLot));
}

bool IsTradingAllowedNow()
{
   if(!IsExpertEnabled()) return false;
   if(!IsTradeAllowed())  return false;
   if(AccountStopoutMode()==0) {} // no-op, just keep footprint clean
   if(g_circuitTripped)   return false;
   // You can add trading hours, holiday file gates, etc. here.
   return true;
}

void InfoLog(string msg)
{
   Print("[INFO] ", msg);
}

void WarnLog(string msg)
{
   Print("[WARN] ", msg);
}

void ErrorLog(string msg)
{
   Print("[ERROR] ", msg);
}

string TimeToISO(datetime t)
{
   // Format "YYYY-MM-DD HH:MM:SS"
   return StringFormat("%04d-%02d-%02d %02d:%02d:%02d",
      TimeYear(t), TimeMonth(t), TimeDay(t), TimeHour(t), TimeMinute(t), TimeSecond(t));
}

int HashLineId(string s)
{
   // Very simple rolling hash; good enough for duplicate suppression during session
   int h = 0;
   for(int i=0;i<StringLen(s);i++)
      h = (h*131 + StringGetChar(s, i)) & 0x7fffffff;
   if(h==0) h=1;
   return h;
}

bool AlreadyProcessed(string id)
{
   for(int i=0;i<g_processedCount;i++)
      if(g_processedIds[i]==id) return true;
   return false;
}

void MarkProcessed(string id)
{
   if(g_processedCount < ArraySize(g_processedIds))
   {
      g_processedIds[g_processedCount++] = id;
   }
}

// ==========================
// ===== Recording Utils ====
// ==========================

void EnsureResponseHeader()
{
   int h = FileOpen(CSVResponseFile, FILE_READ|FILE_CSV, ';');
   if(h<0)
   {
      int w = FileOpen(CSVResponseFile, FILE_WRITE|FILE_CSV, ';');
      if(w>=0)
      {
         FileWrite(w, "ts","signal_id","source","symbol","order_type","lot","sl","tp","result","ticket","error_code","message");
         FileClose(w);
      }
   }
   else FileClose(h);
}

void WriteResponse(string signalId, string source, string symbol, int orderType, double lot, double sl, double tp, bool ok, int ticket, int err, string message)
{
   EnsureResponseHeader();
   int h = FileOpen(CSVResponseFile, FILE_READ|FILE_WRITE|FILE_CSV, ';');
   if(h<0) return;
   FileSeek(h, 0, SEEK_END);
   FileWrite(h, TimeToISO(TimeCurrent()), signalId, source, symbol, orderType, DoubleToString(lot,2), DoubleToString(sl,Digits), DoubleToString(tp,Digits),
             (ok?"OK":"ERR"), ticket, err, message);
   FileClose(h);
}

// Snapshot basic account+symbol info into journal (extend to CSV if desired)
void LogAccountSymbolSnapshot()
{
   string sym = ScopeSymbol();
   double balance = AccountBalance();
   double equity  = AccountEquity();
   double margin  = AccountMargin();
   double freeMrn = AccountFreeMargin();
   int    openCnt = 0;
   int    pendCnt = 0;
   for(int i=OrdersTotal()-1;i>=0;i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol()!=sym) continue;
      if(OrderMagicNumber()!=Magic) continue;
      if(OrderType()==OP_BUY || OrderType()==OP_SELL) openCnt++;
      else pendCnt++;
   }

   double minLot   = MarketInfo(sym, MODE_MINLOT);
   double maxLot   = MarketInfo(sym, MODE_MAXLOT);
   double lotStep  = MarketInfo(sym, MODE_LOTSTEP);
   double stopLvl  = MarketInfo(sym, MODE_STOPLEVEL)*Point;

   Print(StringFormat("[SNAPSHOT] bal=%.2f eq=%.2f mr=%.2f fm=%.2f open=%d pend=%d lot[min=%.2f,max=%.2f,step=%.2f] stopLevelPts=%.1f",
         balance,equity,margin,freeMrn,openCnt,pendCnt,minLot,maxLot,lotStep,stopLvl/Point));
}

// ==========================
// === Circuit Breaker ======
// ==========================

string EquityPeakGVName()
{
   return StringFormat("HUEY_PEak_%d_%s", AccountNumber(), ScopeSymbol());
}

void LoadEquityPeak()
{
   string gv = EquityPeakGVName();
   if(GlobalVariableCheck(gv)) g_equityPeak = GlobalVariableGet(gv);
   if(g_equityPeak <= 0) g_equityPeak = AccountEquity();
}

void PersistEquityPeak()
{
   string gv = EquityPeakGVName();
   if(!GlobalVariableCheck(gv)) GlobalVariableSet(gv, g_equityPeak);
   else GlobalVariableSet(gv, g_equityPeak);
}

void UpdateEquityPeak()
{
   double eq = AccountEquity();
   if(eq > g_equityPeak)
   {
      g_equityPeak = eq;
      PersistEquityPeak();
   }
}

bool HeartbeatFresh()
{
   if(!EnableHeartbeat) return true;
   int h = FileOpen(HeartbeatFile, FILE_READ|FILE_TXT);
   if(h<0) return false;
   string line = FileReadString(h);
   FileClose(h);
   // accept any content as "recent" if file modify time is fresh enough
   // (MQL4 lacks direct modtime; emulate by requiring timestamp inside file)
   datetime t = (datetime)StringToInteger(line);
   if(t==0) return false;
   return (TimeCurrent() - t) <= PythonHeartbeatTimeoutSec;
}

void CloseAllForScope()
{
   string sym = ScopeSymbol();
   for(int i=OrdersTotal()-1;i>=0;i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol()!=sym) continue;
      if(OrderMagicNumber()!=Magic) continue;

      int type = OrderType();
      bool ok=false;
      if(type==OP_BUY || type==OP_SELL)
      {
         double price = (type==OP_BUY? Bid : Ask);
         int    slippage = SlippagePoints;
         RefreshRates();
         ok = OrderClose(OrderTicket(), OrderLots(), price, slippage, clrRed);
      }
      else
      {
         ok = OrderDelete(OrderTicket());
      }
      if(!ok) Print("[BREAKER] Close failed ticket=", OrderTicket(), " err=", GetLastError());
      Sleep(100);
   }
}

void TripCircuit(string reason)
{
   if(g_circuitTripped) return;
   g_circuitTripped = true;
   ErrorLog("[CIRCUIT-TRIPPED] " + reason);
   if(ClosePositionsOnTrip) CloseAllForScope();
}

void CheckCircuitBreaker()
{
   if(!EnableCircuitBreaker) return;

   UpdateEquityPeak();
   double eq = AccountEquity();
   double dropPct = (g_equityPeak<=0 ? 0 : (g_equityPeak - eq)/g_equityPeak * 100.0);
   if(dropPct >= MaxEquityDrawdownPct)
   {
      TripCircuit(StringFormat("Equity drawdown %.2f%% >= %.2f%%", dropPct, MaxEquityDrawdownPct));
      return;
   }

   if(EnableHeartbeat && !HeartbeatFresh())
   {
      TripCircuit("Python heartbeat stale");
      return;
   }
}

// ==========================
// ===== Order Helpers  =====
// ==========================

bool SafeOrderSend(int type, double lots, double price, double sl, double tp, string comment, int &ticketOut, int &lastErr)
{
   lots  = NormalizeLot(lots);
   ticketOut = -1;
   lastErr   = 0;

   for(int attempt=0; attempt<=OrderRetryAttempts; attempt++)
   {
      RefreshRates();
      double sendPrice = price;
      int    slippage  = SlippagePoints;

      // For market orders, price parameter must be current Bid/Ask
      if(type==OP_BUY || type==OP_SELL)
      {
         sendPrice = (type==OP_BUY ? Ask : Bid);
      }

      int ticket = OrderSend(ScopeSymbol(), type, lots, sendPrice, slippage, sl, tp, comment, Magic, 0, clrNONE);
      if(ticket>0)
      {
         ticketOut = ticket;
         return true;
      }
      lastErr = GetLastError();
      WarnLog(StringFormat("OrderSend failed (type=%d, lots=%.2f) err=%d, attempt=%d", type, lots, lastErr, attempt+1));
      Sleep(OrderRetryDelayMs);
   }
   return false;
}

bool ComputeSLTP(int type, double entryPrice, double slPips, double tpPips, double &sl, double &tp)
{
   double pip = PipValueInPoints();
   if(type==OP_BUY || type==OP_BUYSTOP || type==OP_BUYLIMIT)
   {
      sl = (slPips>0 ? entryPrice - slPips*pip : 0);
      tp = (tpPips>0 ? entryPrice + tpPips*pip : 0);
   }
   else
   {
      sl = (slPips>0 ? entryPrice + slPips*pip : 0);
      tp = (tpPips>0 ? entryPrice - tpPips*pip : 0);
   }
   return true;
}

// ==========================
// ===== Tier 1: Auto  ======
// ==========================

void TryPlaceAutonomousStraddle()
{
   if(!AutonomousMode || !AutoPlaceStraddle) return;
   if(!IsTradingAllowedNow()) return;

   string sym = ScopeSymbol();
   // Do not place another straddle if pending orders already exist for scope
   for(int i=OrdersTotal()-1;i>=0;i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol()!=sym) continue;
      if(OrderMagicNumber()!=Magic) continue;
      if(OrderType()==OP_BUYSTOP || OrderType()==OP_SELLSTOP || OrderType()==OP_BUYLIMIT || OrderType()==OP_SELLLIMIT)
         return; // existing pending
   }

   RefreshRates();
   double pip  = PipValueInPoints();
   double buyStop  = Ask + StraddleDistancePips * pip;
   double sellStop = Bid - StraddleDistancePips * pip;

   double sl=0,tp=0;
   // simple placeholders (0=broker-side none). Adjust to your policy or add inputs
   int ticket, err;
   bool ok1=false, ok2=false;

   ok1 = SafeOrderSend(OP_BUYSTOP, StraddleLotSize, buyStop, sl, tp, "AUTO_STRADDLE", ticket, err);
   if(ok1) InfoLog(StringFormat("Placed BUYSTOP ticket=%d @ %.5f", ticket, buyStop));
   else    WriteResponse("auto-straddle-buystop", "AUTONOMOUS", sym, OP_BUYSTOP, StraddleLotSize, sl, tp, false, -1, err, "OrderSend BUYSTOP failed");

   ok2 = SafeOrderSend(OP_SELLSTOP, StraddleLotSize, sellStop, sl, tp, "AUTO_STRADDLE", ticket, err);
   if(ok2) InfoLog(StringFormat("Placed SELLSTOP ticket=%d @ %.5f", ticket, sellStop));
   else    WriteResponse("auto-straddle-sellstop", "AUTONOMOUS", sym, OP_SELLSTOP, StraddleLotSize, sl, tp, false, -1, err, "OrderSend SELLSTOP failed");
}

// ==========================
// ===== Tier 2: CSV   ======
// ==========================

bool ParseCSVSignal(string line, CSVSignal &sig, string &idOut)
{
   // Expected format (semicolon-separated):
   // ts;symbol;order_type;lot;sl;tp;comment
   // ts may be ISO "YYYY-MM-DD HH:MM:SS" or integer TimeLocal()
   string parts[];
   int n = StringSplit(line, ';', parts);
   if(n < 7) return false;

   string ts = parts[0];
   if(StringLen(ts)==19 && StringFind(ts, "-")>=0)
      sig.executionTime = StringToTime(ts);
   else
      sig.executionTime = (datetime)StringToInteger(ts);

   sig.symbol    = parts[1];
   sig.orderType = (int)StringToInteger(parts[2]);
   sig.lot       = StrToDouble(parts[3]);
   sig.sl        = StrToDouble(parts[4]);
   sig.tp        = StrToDouble(parts[5]);
   sig.comment   = parts[6];

   idOut = IntegerToString(HashLineId(line));
   return true;
}

void ProcessCSVSignals()
{
   if(!EnableCSVSignals) return;
   static datetime lastRead = 0;
   if((TimeCurrent() - g_lastCSVCheck) < CSVCheckIntervalSeconds) return;
   g_lastCSVCheck = TimeCurrent();

   // Always (re)open and stream through file; suppress duplicates via id hash
   int h = FileOpen(CSVSignalFile, FILE_READ|FILE_CSV, ';');
   if(h<0)
      return;

   while(!FileIsEnding(h))
   {
      string ts = FileReadString(h);
      if(StringLen(ts)==0) { FileReadString(h); FileReadString(h); FileReadString(h); FileReadString(h); FileReadString(h); FileReadString(h); continue; } // skip blank row
      string sym = FileReadString(h);
      string otype= FileReadString(h);
      string lot = FileReadString(h);
      string sl   = FileReadString(h);
      string tp   = FileReadString(h);
      string cmt  = FileReadString(h);

      string raw = ts+";"+sym+";"+otype+";"+lot+";"+sl+";"+tp+";"+cmt;
      CSVSignal sig;
      string id;
      if(!ParseCSVSignal(raw, sig, id)) continue;
      if(AlreadyProcessed(id)) continue;

      // Symbol gate
      string scope = ScopeSymbol();
      if(sig.symbol!=scope) { continue; }

      // Time gate
      int dt = MathAbs((int)(TimeCurrent() - sig.executionTime));
      if(dt > SignalExecutionToleranceSeconds) continue; // not due right now

      // Execute
      if(!IsTradingAllowedNow())
      {
         WriteResponse(id, "CSV", sig.symbol, sig.orderType, sig.lot, sig.sl, sig.tp, false, -1, 0, "Trading not allowed now");
         MarkProcessed(id);
         continue;
      }

      int ticket, err;
      double price = 0;
      if(sig.orderType==OP_BUY || sig.orderType==OP_SELL) price=0; // market
      else if(sig.orderType==OP_BUYLIMIT || sig.orderType==OP_SELLLIMIT || sig.orderType==OP_BUYSTOP || sig.orderType==OP_SELLSTOP)
      {
         // If sl field was reused for price, allow that (optional). Here we assume comment "price=xxx" optional.
         // For simplicity, use current price +- small offset if none is provided. In practice, pass a proper price.
         RefreshRates();
         if(sig.orderType==OP_BUYSTOP)      price = Ask + 1*PipValueInPoints();
         else if(sig.orderType==OP_SELLSTOP) price = Bid - 1*PipValueInPoints();
         else if(sig.orderType==OP_BUYLIMIT) price = Bid - 1*PipValueInPoints();
         else if(sig.orderType==OP_SELLLIMIT)price = Ask + 1*PipValueInPoints();
      }

      bool ok = SafeOrderSend(sig.orderType, sig.lot, price, sig.sl, sig.tp, sig.comment, ticket, err);
      WriteResponse(id, "CSV", sig.symbol, sig.orderType, sig.lot, sig.sl, sig.tp, ok, (ok?ticket:-1), (ok?0:err), (ok?"OK":"OrderSend failed"));
      MarkProcessed(id);
   }

   FileClose(h);
}

// ==========================
// ===== Tier 3: DLL   ======
// ==========================

// Minimal JSON helpers (expects flat {"k":"v", "n":123} JSON)
string JsonGet(string json, string key)
{
   // Find "key": ... extract value as string (handles quoted or numeric/bool)
   string pat = "\""+key+"\"";
   int pos = StringFind(json, pat);
   if(pos<0) return "";
   pos = StringFind(json, ":", pos);
   if(pos<0) return "";
   // Skip spaces
   while(pos<StringLen(json) && (StringGetChar(json,pos)==':' || StringGetChar(json,pos)==' ')) pos++;

   // Quoted?
   if(StringGetChar(json,pos)=='\"')
   {
      pos++;
      int end = StringFind(json, "\"", pos);
      if(end<0) return "";
      return StringSubstr(json, pos, end-pos);
   }
   // Read until comma or close brace
   int end2 = pos;
   while(end2<StringLen(json))
   {
      int ch = StringGetChar(json,end2);
      if(ch==',' || ch=='}') break;
      end2++;
   }
   string raw = StringSubstr(json, pos, end2-pos);
   // trim spaces
   while(StringLen(raw)>0 && StringGetChar(raw,0)==' ')  raw = StringSubstr(raw,1);
   while(StringLen(raw)>0 && StringGetChar(raw,StringLen(raw)-1)==' ') raw = StringSubstr(raw,0,StringLen(raw)-1);
   return raw;
}

int ToInt(string s) { return (int)StrToDouble(s); }
double ToDouble(string s) { return StrToDouble(s); }

void ExecuteDLLSignalJSON(string json)
{
   g_dllSignalProcessing = true;
   string id     = JsonGet(json, "signal_id"); if(id=="") id = IntegerToString(HashLineId(json));
   string symbol = JsonGet(json, "symbol");    if(symbol=="") symbol = ScopeSymbol();
   string typeS  = JsonGet(json, "order_type");
   string lotS   = JsonGet(json, "lot");
   string slS    = JsonGet(json, "stop_loss");
   string tpS    = JsonGet(json, "take_profit");
   string cmt    = JsonGet(json, "comment");

   int    type = ToInt(typeS);
   double lot  = ToDouble(lotS);
   double sl   = ToDouble(slS);
   double tp   = ToDouble(tpS);

   if(symbol != ScopeSymbol())
   {
      WriteResponse(id, "DLL", symbol, type, lot, sl, tp, false, -1, 0, "Symbol mismatch");
      g_dllSignalProcessing = false;
      return;
   }
   if(!IsTradingAllowedNow())
   {
      WriteResponse(id, "DLL", symbol, type, lot, sl, tp, false, -1, 0, "Trading not allowed now");
      g_dllSignalProcessing = false;
      return;
   }

   int ticket, err;
   double price = 0;
   if(type==OP_BUY || type==OP_SELL) price=0; else
   {
      RefreshRates();
      if(type==OP_BUYSTOP)      price = Ask + 1*PipValueInPoints();
      else if(type==OP_SELLSTOP) price = Bid - 1*PipValueInPoints();
      else if(type==OP_BUYLIMIT) price = Bid - 1*PipValueInPoints();
      else if(type==OP_SELLLIMIT)price = Ask + 1*PipValueInPoints();
   }

   bool ok = SafeOrderSend(type, lot, price, sl, tp, cmt, ticket, err);
   WriteResponse(id, "DLL", symbol, type, lot, sl, tp, ok, (ok?ticket:-1), (ok?0:err), (ok?"OK":"OrderSend failed"));
   g_dllSignalProcessing = false;
}

void StartSocketIfEnabled()
{
   if(!EnableDLLSignals) return;
   // Start server and store socket id; in this minimal stub we'll assume socketId==1 when started
   int res = StartServer(ListenPort, 0, CUSTOM_EVENT_ID);
   if(res<=0)
   {
      ErrorLog("StartServer failed; DLL may be missing or DLL imports not allowed. Disable EnableDLLSignals to suppress.");
      return;
   }
   g_socketId = res;
   InfoLog(StringFormat("Socket server started on port %d (id=%d)", ListenPort, g_socketId));
}

// ==========================
// ===== Meta Callbacks =====
// ==========================

int OnInit()
{
   LoadEquityPeak();
   EventSetTimer(1);
   EnsureResponseHeader();
   StartSocketIfEnabled();
   InfoLog("EA initialized. Three-tier communication online.");
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   if(EnableDLLSignals) StopServer();
   InfoLog("EA deinitialized.");
}

void OnTick()
{
   CheckCircuitBreaker();
   if(EnableCommentHUD)
   {
      string hud = StringFormat("HUEY_P Three-Tier EA\nSymbol: %s  Magic: %d\nEquityPeak: %.2f  Equity: %.2f  Tripped: %s\nAuto:%s CSV:%s DLL:%s",
         ScopeSymbol(), Magic, g_equityPeak, AccountEquity(), (g_circuitTripped?"YES":"NO"),
         (AutonomousMode?"ON":"OFF"), (EnableCSVSignals?"ON":"OFF"), (EnableDLLSignals?"ON":"OFF"));
      Comment(hud);
   }

   if(!g_circuitTripped)
   {
      TryPlaceAutonomousStraddle();
   }
}

void OnTimer()
{
   CheckCircuitBreaker();
   if(!g_dllSignalProcessing) ProcessCSVSignals();

   // Optional: periodic snapshots (commented out to reduce noise)
   // LogAccountSymbolSnapshot();
}

void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
   if(id==CUSTOM_EVENT_ID)
   {
      // DLL posted a message; sparam expected to be JSON text
      ExecuteDLLSignalJSON(sparam);
   }
}

// ==========================
// ======= End of EA ========
// ==========================
