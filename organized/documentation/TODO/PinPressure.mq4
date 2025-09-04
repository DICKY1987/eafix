
//+------------------------------------------------------------------+
//|                                               PinPressure.mq4    |
//| Simple oscillator (0..100) from nearest strike pin_score         |
//| Fetches CSV from the same local API as ExpiryZones.mq4           |
//+------------------------------------------------------------------+
#property strict
#property indicator_separate_window
#property indicator_buffers 2
#property indicator_plots   1
#property indicator_label1  "PinPressure"
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrLime
#property indicator_style1  STYLE_SOLID
#property indicator_width1  2

double BufferPin[];
double BufferDist[];

input string InpBaseUrl        = "http://127.0.0.1:5001";
input int    InpRefreshSeconds = 30;
input bool   InpUseCSV         = true;

int OnInit()
{
   SetIndexBuffer(0, BufferPin, INDICATOR_DATA);
   SetIndexBuffer(1, BufferDist, INDICATOR_CALCULATIONS);
   ArraySetAsSeries(BufferPin, true);
   ArraySetAsSeries(BufferDist, true);
   IndicatorShortName("PinPressure (nearest strike pin score)");
   EventSetTimer(InpRefreshSeconds);
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   EventKillTimer();
}

double PipInPrice()
{
   if(Digits==3 || Digits==5) return (10*Point);
   return Point;
}

bool HttpGet(const string url, string &result)
{
   char data[];
   string headers;
   char res[];
   ResetLastError();
   int status = WebRequest("GET", url, headers, 5000, data, 0, res, headers);
   if(status==200)
   {
      result = CharArrayToString(res,0,ArraySize(res));
      return true;
   }
   Print("WebRequest failed: status=",status," err=",GetLastError()," url=",url);
   return false;
}

void UpdateFromCSV(const string body)
{
   // columns: symbol,strike,ccy,notional,size_rank,expiry_ts_utc,spot,distance_pips,pin_score,pre_post
   string lines[]; int n = StringSplit(body, '\n', lines);
   if(n<=1) return;
   double bestDist = 1e9;
   double bestPin  = 0.0;
   for(int i=1;i<n;i++)
   {
      string line = StringTrim(lines[i]);
      if(line=="") continue;
      string cols[]; int c = StringSplit(line, ',', cols);
      if(c<10) continue;
      if(cols[0]!=Symbol()) continue;
      double dist = StrToDouble(cols[7]);
      double pin  = StrToDouble(cols[8]);
      if(dist<bestDist)
      {
         bestDist = dist;
         bestPin  = pin;
      }
   }
   int shift = 0;
   BufferPin[shift]  = bestPin;
   BufferDist[shift] = bestDist;
}

int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   // keep last value; drawing is timer-driven
   return(rates_total);
}

void OnTimer()
{
   string route = InpUseCSV ? "/expiries.csv?symbol=" : "/expiries?symbol=";
   string url   = InpBaseUrl + route + Symbol();
   string body;
   if(!HttpGet(url, body)) return;

   if(InpUseCSV)
      UpdateFromCSV(body);
   else
   {
      // naive JSON parse: find nearest by smallest "distance_pips"
      double bestDist = 1e9;
      double bestPin  = 0.0;
      int pos = 0;
      while(true)
      {
         int id = StringFind(body, "\"distance_pips\":", pos);
         if(id<0) break;
         int comma = StringFind(body, ",", id+16);
         double dist = StrToDouble(StringSubstr(body, id+16, comma-(id+16)));
         int ip = StringFind(body, "\"pin_score\":", comma);
         int comma2 = StringFind(body, ",", ip+12);
         double pin = StrToDouble(StringSubstr(body, ip+12, comma2-(ip+12)));
         if(dist<bestDist){ bestDist=dist; bestPin=pin; }
         pos = comma2+1;
      }
      BufferPin[0]  = bestPin;
      BufferDist[0] = bestDist;
   }
}
