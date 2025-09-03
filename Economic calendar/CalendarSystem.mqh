//+------------------------------------------------------------------+
//| CalendarSystem.mqh                                               |
//+------------------------------------------------------------------+
#property strict
#include "CommonTypes.mqh"
#include "ParameterManager.mqh"

#ifndef __CALENDAR_SYSTEM_MQH__
#define __CALENDAR_SYSTEM_MQH__

class CCalendarSystem {
private:
   EconomicEvent m_events[200];
   int           m_event_count;
   int           m_last_param;
public:
   CCalendarSystem(): m_event_count(0), m_last_param(0) {}

   bool Initialize(const string config_file=""){ return true; }
   int  GetActiveEventCount() const { return 0; }

   // Very simple signal generator from an event (stubbed)
   SignalData CreateCalendarSignal(const EconomicEvent &event){
      SignalData s;
      s.signal_id = "CAL_"+event.event_id+"_"+IntegerToString((int)TimeCurrent());
      s.symbol    = Symbol();
      s.signal_type="CALENDAR";
      s.source    = "CALENDAR_SYSTEM";
      s.signal_time= TimeCurrent();
      s.parameter_set_id = event.parameter_set_id>0?event.parameter_set_id:1;
      s.direction = (event.impact=="High" ? "BUY" : "SELL");
      s.confidence= (event.impact=="High" ? 0.8 : (event.impact=="Medium"?0.6:0.4));
      s.lot_size  = 0.01*s.parameter_set_id;
      s.metadata  = "Event: "+event.title;
      return s;
   }
};

#endif // __CALENDAR_SYSTEM_MQH__
