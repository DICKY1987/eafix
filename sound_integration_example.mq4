//+------------------------------------------------------------------+
//|                                  sound_integration_example.mq4   |
//|               Example of integrating sound notifications         |
//|                  into HUEY_P Trading System EA                   |
//+------------------------------------------------------------------+

// Include the sound manager
#include "trade_sound_manager.mqh"

// Your existing EA code here...
// This example shows key integration points

//+------------------------------------------------------------------+
//| Example: Integration into your EA's trade execution              |
//+------------------------------------------------------------------+

// Example function showing how to integrate sounds into trade opening
int OpenTradeWithSound(int orderType, double lotSize, string comment = "")
{
    double price = (orderType == OP_BUY) ? Ask : Bid;
    double stopLoss = 0;   // Calculate your SL
    double takeProfit = 0; // Calculate your TP
    
    // Attempt to open the trade
    int ticket = OrderSend(
        Symbol(),           // Symbol
        orderType,          // Order type (OP_BUY or OP_SELL)
        lotSize,           // Lot size
        price,             // Price
        Slippage,          // Slippage
        stopLoss,          // Stop loss
        takeProfit,        // Take profit
        comment,           // Comment
        MagicNumber,       // Magic number
        0,                 // Expiration
        (orderType == OP_BUY) ? clrBlue : clrRed  // Color
    );
    
    // Check if trade was successful
    if(ticket > 0)
    {
        // *** THIS IS WHERE THE MAGIC HAPPENS ***
        // Play the "you-are-watching-a-master-at-work.mp3" sound
        NotifyTradeEntry(ticket, Symbol(), orderType);
        
        Print("✅ TRADE OPENED - Master at work! Ticket: ", ticket, 
              " Type: ", (orderType == OP_BUY ? "BUY" : "SELL"),
              " Size: ", DoubleToString(lotSize, 2));
        
        return ticket;
    }
    else
    {
        // Play error sound and log
        int error = GetLastError();
        string errorMsg = "Failed to open " + (orderType == OP_BUY ? "BUY" : "SELL") + 
                         " trade - Error: " + IntegerToString(error);
        
        NotifyTradeError(errorMsg);
        Print("❌ TRADE FAILED: ", errorMsg);
        
        return -1;
    }
}

// Example function showing how to integrate sounds into trade closing
bool CloseTradeWithSound(int ticket)
{
    if(!OrderSelect(ticket, SELECT_BY_TICKET))
    {
        NotifyTradeError("Cannot select order ticket: " + IntegerToString(ticket));
        return false;
    }
    
    double closePrice = (OrderType() == OP_BUY) ? Bid : Ask;
    double profit = OrderProfit() + OrderSwap() + OrderCommission();
    
    // Attempt to close the trade
    bool result = OrderClose(
        ticket,           // Ticket
        OrderLots(),      // Lots
        closePrice,       // Close price
        Slippage,         // Slippage
        (OrderType() == OP_BUY) ? clrRed : clrBlue  // Color
    );
    
    if(result)
    {
        // *** PLAY CLOSE SOUND WITH WIN/LOSS DETECTION ***
        NotifyTradeClose(ticket, profit);
        
        string resultText = (profit > 0) ? "WIN ✅" : (profit < 0) ? "LOSS ❌" : "BREAKEVEN ➖";
        Print("🔚 TRADE CLOSED - ", resultText, " Ticket: ", ticket, 
              " Profit: ", DoubleToString(profit, 2));
              
        return true;
    }
    else
    {
        int error = GetLastError();
        NotifyTradeError("Failed to close trade " + IntegerToString(ticket) + 
                        " - Error: " + IntegerToString(error));
        return false;
    }
}

//+------------------------------------------------------------------+
//| Integration into OnTick() - Example Pattern                     |
//+------------------------------------------------------------------+
void OnTick()
{
    // Your existing trading logic here...
    
    // Example: When your trading signal triggers
    if(YourBuySignalCondition())
    {
        double lotSize = CalculateLotSize(); // Your lot calculation
        int ticket = OpenTradeWithSound(OP_BUY, lotSize, "HUEY_P_Master_Buy");
        
        if(ticket > 0)
        {
            // Store ticket for management
            // Your position management code here...
        }
    }
    
    if(YourSellSignalCondition())
    {
        double lotSize = CalculateLotSize(); // Your lot calculation  
        int ticket = OpenTradeWithSound(OP_SELL, lotSize, "HUEY_P_Master_Sell");
        
        if(ticket > 0)
        {
            // Store ticket for management
            // Your position management code here...
        }
    }
    
    // Example: Check for trade exit conditions
    CheckAndCloseTradesWithSound();
}

// Helper function to check and close trades with sound
void CheckAndCloseTradesWithSound()
{
    for(int i = OrdersTotal() - 1; i >= 0; i--)
    {
        if(OrderSelect(i, SELECT_BY_POS) && OrderSymbol() == Symbol() && OrderMagicNumber() == MagicNumber)
        {
            // Your exit logic here (SL/TP hit, time exit, signal reversal, etc.)
            if(YourExitCondition())
            {
                CloseTradeWithSound(OrderTicket());
            }
        }
    }
}

// Placeholder functions - replace with your actual trading logic
bool YourBuySignalCondition() { return false; }   // Implement your buy signal
bool YourSellSignalCondition() { return false; }  // Implement your sell signal
bool YourExitCondition() { return false; }        // Implement your exit logic
double CalculateLotSize() { return 0.01; }        // Implement your lot sizing

//+------------------------------------------------------------------+
//| QUICK SETUP CHECKLIST                                           |
//+------------------------------------------------------------------+
/*
✅ SETUP CHECKLIST:

1. SOUND FILE PLACEMENT:
   - Copy "you-are-watching-a-master-at-work.mp3" to:
     MT4_Data_Folder\Sounds\you-are-watching-a-master-at-work.mp3

2. FIND YOUR MT4 SOUNDS FOLDER:
   - Open MT4 → File → Open Data Folder → Sounds folder
   - Or typically: C:\Users\[Username]\AppData\Roaming\MetaQuotes\Terminal\[ID]\Sounds\

3. EA INTEGRATION:
   - Add #include "trade_sound_manager.mqh" to your EA
   - Replace OrderSend() calls with OpenTradeWithSound()
   - Replace OrderClose() calls with CloseTradeWithSound()

4. TEST SOUND:
   - In MT4: Tools → Options → Events → Enable sound alerts
   - Run EA in strategy tester or demo account
   - Verify sound plays when trades execute

5. CUSTOMIZATION:
   - Modify input parameters to change sound files
   - Enable/disable specific sound types in EA inputs
   - Add custom sounds for other events

The sound will play EVERY TIME a trade is entered automatically!
*/