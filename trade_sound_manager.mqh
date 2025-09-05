//+------------------------------------------------------------------+
//|                                        trade_sound_manager.mqh    |
//|                        Trading Sound Manager for HUEY_P EA       |
//|                    Copyright 2025, HUEY_P Trading Systems        |
//+------------------------------------------------------------------+

#property copyright "Copyright 2025, HUEY_P Trading Systems"
#property strict

//+------------------------------------------------------------------+
//| Sound Configuration Parameters                                   |
//+------------------------------------------------------------------+
input group "--- Sound Notification Settings ---"
input bool   EnableSoundAlerts = true;           // Enable/disable all sound alerts
input bool   PlaySoundOnTradeEntry = true;       // Play sound when trade is opened
input bool   PlaySoundOnTradeClose = true;       // Play sound when trade is closed
input bool   PlaySoundOnWinTrade = true;         // Play sound on winning trades
input bool   PlaySoundOnLossTrade = true;        // Play sound on losing trades
input bool   PlaySoundOnErrors = true;           // Play sound on trade errors

input string TradeEntrySoundFile = "you-are-watching-a-master-at-work.mp3";  // Sound file for trade entry
input string TradeCloseSoundFile = "close.wav";     // Sound file for trade close
input string WinSoundFile = "ok.wav";              // Sound file for winning trades
input string LossSoundFile = "timeout.wav";        // Sound file for losing trades
input string ErrorSoundFile = "error.wav";         // Sound file for errors

//+------------------------------------------------------------------+
//| TradeSoundManager Class                                          |
//+------------------------------------------------------------------+
class TradeSoundManager
{
private:
    bool soundsEnabled;
    string soundsFolder;
    
public:
    // Constructor
    TradeSoundManager()
    {
        soundsEnabled = EnableSoundAlerts;
        soundsFolder = TerminalInfoString(TERMINAL_DATA_PATH) + "\\Sounds\\";
        
        // Verify sound files exist
        VerifySoundFiles();
    }
    
    // Main sound playing method
    void PlayTradeSound(string soundType, string context = "")
    {
        if(!soundsEnabled) return;
        
        string soundFile = "";
        bool shouldPlay = false;
        
        if(soundType == "TRADE_ENTRY" && PlaySoundOnTradeEntry)
        {
            soundFile = TradeEntrySoundFile;
            shouldPlay = true;
        }
        else if(soundType == "TRADE_CLOSE" && PlaySoundOnTradeClose)
        {
            soundFile = TradeCloseSoundFile;
            shouldPlay = true;
        }
        else if(soundType == "WIN_TRADE" && PlaySoundOnWinTrade)
        {
            soundFile = WinSoundFile;
            shouldPlay = true;
        }
        else if(soundType == "LOSS_TRADE" && PlaySoundOnLossTrade)
        {
            soundFile = LossSoundFile;
            shouldPlay = true;
        }
        else if(soundType == "ERROR" && PlaySoundOnErrors)
        {
            soundFile = ErrorSoundFile;
            shouldPlay = true;
        }
        
        if(shouldPlay && StringLen(soundFile) > 0)
        {
            // Play the sound
            bool result = PlaySound(soundFile);
            
            if(!result && StringLen(context) > 0)
            {
                Print("[SOUND_MGR] Failed to play sound: ", soundFile, " | Context: ", context);
            }
            else if(result)
            {
                Print("[SOUND_MGR] Playing sound: ", soundFile, " | Context: ", context);
            }
        }
    }
    
    // Specific sound methods for different events
    void PlayTradeEntrySound(int ticket, string symbol, int orderType)
    {
        string context = "Ticket:" + IntegerToString(ticket) + " Symbol:" + symbol + 
                        " Type:" + (orderType == OP_BUY ? "BUY" : "SELL");
        PlayTradeSound("TRADE_ENTRY", context);
    }
    
    void PlayTradeCloseSound(int ticket, double profit)
    {
        string context = "Ticket:" + IntegerToString(ticket) + " Profit:" + DoubleToString(profit, 2);
        PlayTradeSound("TRADE_CLOSE", context);
    }
    
    void PlayWinSound(int ticket, double profit)
    {
        string context = "WIN - Ticket:" + IntegerToString(ticket) + " Profit:+" + DoubleToString(profit, 2);
        PlayTradeSound("WIN_TRADE", context);
    }
    
    void PlayLossSound(int ticket, double profit)
    {
        string context = "LOSS - Ticket:" + IntegerToString(ticket) + " Loss:" + DoubleToString(profit, 2);
        PlayTradeSound("LOSS_TRADE", context);
    }
    
    void PlayErrorSound(string errorMsg)
    {
        PlayTradeSound("ERROR", errorMsg);
    }
    
    // Utility methods
    void EnableSounds(bool enable)
    {
        soundsEnabled = enable;
        Print("[SOUND_MGR] Sound notifications ", (enable ? "ENABLED" : "DISABLED"));
    }
    
    bool AreSoundsEnabled()
    {
        return soundsEnabled;
    }
    
    void VerifySoundFiles()
    {
        VerifyFile(TradeEntrySoundFile, "Trade Entry");
        VerifyFile(TradeCloseSoundFile, "Trade Close");
        VerifyFile(WinSoundFile, "Win Trade");
        VerifyFile(LossSoundFile, "Loss Trade");  
        VerifyFile(ErrorSoundFile, "Error");
    }
    
private:
    void VerifyFile(string filename, string description)
    {
        if(StringLen(filename) == 0) return;
        
        string fullPath = soundsFolder + filename;
        
        // Check if file exists (basic check - MT4 will validate when playing)
        Print("[SOUND_MGR] ", description, " sound file configured: ", filename);
        
        // Note: You should manually verify the file exists in MetaTrader's Sounds folder
        // Path: [MT4_DATA_FOLDER]\\Sounds\\[filename]
    }
};

//+------------------------------------------------------------------+
//| Global Sound Manager Instance                                    |
//+------------------------------------------------------------------+
TradeSoundManager g_tradeSoundManager;

//+------------------------------------------------------------------+
//| Sound Integration Helper Functions                               |
//+------------------------------------------------------------------+

// Call this when a trade is successfully opened
void NotifyTradeEntry(int ticket, string symbol, int orderType)
{
    g_tradeSoundManager.PlayTradeEntrySound(ticket, symbol, orderType);
}

// Call this when a trade is closed
void NotifyTradeClose(int ticket, double profit)
{
    g_tradeSoundManager.PlayTradeCloseSound(ticket, profit);
    
    // Also play win/loss specific sound
    if(profit > 0)
        g_tradeSoundManager.PlayWinSound(ticket, profit);
    else if(profit < 0)
        g_tradeSoundManager.PlayLossSound(ticket, profit);
}

// Call this for trade errors
void NotifyTradeError(string errorMsg)
{
    g_tradeSoundManager.PlayErrorSound(errorMsg);
}

//+------------------------------------------------------------------+
//| Installation Instructions                                         |
//+------------------------------------------------------------------+
/*
TO INSTALL THIS SOUND SYSTEM:

1. COPY SOUND FILE:
   - Copy "you-are-watching-a-master-at-work.mp3" to: 
     [MT4_DATA_FOLDER]\Sounds\
   - Example path: C:\Users\[Username]\AppData\Roaming\MetaQuotes\Terminal\[TERMINAL_ID]\Sounds\

2. INCLUDE IN YOUR EA:
   - Add this line at the top of your EA after other includes:
     #include "trade_sound_manager.mqh"

3. ADD TO TRADE EXECUTION CODE:
   - When opening a trade, after successful OrderSend():
     NotifyTradeEntry(ticket, symbol, orderType);
   
   - When closing a trade, after successful OrderClose():
     NotifyTradeClose(ticket, profit);
   
   - For trade errors:
     NotifyTradeError("Error description");

4. EXAMPLE INTEGRATION:
   ```mql4
   int ticket = OrderSend(Symbol(), OP_BUY, lotSize, Ask, slippage, 0, 0, comment, magicNumber);
   if(ticket > 0)
   {
       NotifyTradeEntry(ticket, Symbol(), OP_BUY);
       Print("Trade opened successfully: ", ticket);
   }
   else
   {
       NotifyTradeError("Failed to open trade - Error: " + IntegerToString(GetLastError()));
   }
   ```

5. SOUND FILE FORMATS:
   - Supported: .wav, .mp3 (recommended: .wav for faster loading)
   - Place all sound files in the MT4 Sounds folder
   - Default MT4 sounds available: alert.wav, alert2.wav, connect.wav, disconnect.wav, 
     email.wav, expert.wav, news.wav, ok.wav, stops.wav, tick.wav, timeout.wav, wait.wav

6. CUSTOMIZATION:
   - Modify the input parameters at the top to change default sound files
   - Enable/disable specific sound types through EA inputs
   - Add custom sound events by calling g_tradeSoundManager.PlayTradeSound()
*/