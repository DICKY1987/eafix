# Automated ForexFactory Calendar System - Installation Guide

## Quick Setup (5 Minutes)

### 1. Install Required Dependencies
```bash
# Install Python packages
pip install selenium webdriver-manager pandas schedule

# Or install all at once:
pip install selenium webdriver-manager pandas schedule openpyxl
```

### 2. Download the Script
Save the `ff_auto_downloader.py` script to your desired directory.

### 3. Run the System

**Option A: Run Once (Test)**
```bash
python ff_auto_downloader.py --run-once
```

**Option B: Schedule Automatic Runs (Sunday 12 PM)**
```bash
python ff_auto_downloader.py --schedule
```

**Option C: Custom Output Directory**
```bash
python ff_auto_downloader.py --run-once --output-dir "C:\Your\Custom\Path"
```

## What It Does Automatically

### 🔄 **Complete Automation Process**
1. **Downloads** ForexFactory CSV automatically (no browser interaction needed)
2. **Filters** to High/Medium impact events only (removes Low and CHF)
3. **Creates anticipation events** (1h, 2h, 4h before major announcements)
4. **Adds equity market opens** (Tokyo 21:00, London 02:00, NY 08:30 CST)
5. **Generates strategy IDs** using your RCI system
6. **Outputs MT4-ready CSV** with all events processed

### 📁 **File Organization**
```
Your Directory/
├── ff_auto_downloader.py          # Main script
├── processed_calendar/             # Output folder (MT4-ready CSVs)
├── calendar_archive/               # Archived original downloads
└── calendar_downloader.log        # System logs
```

### 📊 **Output Format**
The final CSV contains:
- **Original economic events** (High/Medium impact only)
- **Anticipation events** ("2H Before NFP Anticipation")
- **Equity market opens** ("London Market Open") 
- **Strategy IDs** (5-digit RCI format: 21102 = Europe-EUR-High)
- **MT4 parameters** (lots, SL, TP, timing windows)

## Integration with Your Existing System

### 🔗 **Seamless Integration**
This script **perfectly integrates** with your existing Economic Calendar System:

1. **Uses your CSV format** (Title, Country, Date, Time, Impact, Forecast, Previous, URL)
2. **Matches your filtering logic** (High/Medium only, excludes CHF, weekend blocking)
3. **Creates your anticipation events** (same naming convention)
4. **Generates your strategy IDs** (RCI system: Region-Country-Impact)
5. **Outputs MT4-compatible format** (semicolon-separated for EA consumption)

### 🕐 **Scheduling Options**

**Option 1: Replace Manual Downloads**
```bash
# Run every Sunday at 12 PM (matches your current schedule)
python ff_auto_downloader.py --schedule
```

**Option 2: Integrate with Windows Task Scheduler**
1. Open Windows Task Scheduler
2. Create Basic Task
3. Set trigger: Weekly, Sunday, 12:00 PM
4. Set action: Start program `python ff_auto_downloader.py --run-once`

**Option 3: Add to Your VBA System**
```vba
' Add this to your existing calendar import module
Private Sub AutomatedCalendarDownload()
    Dim result As Integer
    result = Shell("python ff_auto_downloader.py --run-once", vbNormalFocus)
    
    If result > 0 Then
        ' Continue with your existing processing
        Call ProcessDownloadedCalendar
    End If
End Sub
```

## Configuration Options

### 📝 **Customization**
Edit these settings in the script:

```python
# Anticipation settings
ANTICIPATION_HOURS = [1, 2, 4]  # Hours before events
MAX_ANTICIPATION_EVENTS = 3     # Max per event

# Market opens (CST times)
EQUITY_MARKET_OPENS = {
    "Tokyo": {"time": "21:00", "pairs": ["USDJPY", "AUDJPY"]},
    "London": {"time": "02:00", "pairs": ["EURUSD", "GBPUSD"]},
    "New York": {"time": "08:30", "pairs": ["EURUSD", "USDCAD"]}
}

# Filtering
VALID_IMPACTS = ["High", "Medium"]  # Only High (Red) and Medium (Orange)
EXCLUDED_COUNTRIES = ["CHF"]        # Exclude Switzerland
```

## Troubleshooting

### ❗ **Common Issues**

**1. Chrome Driver Issues**
```bash
# The script auto-downloads ChromeDriver, but if issues occur:
pip install --upgrade webdriver-manager
```

**2. Download Folder Access**
```bash
# Make sure Downloads folder is accessible
# Default: C:\Users\[Username]\Downloads
```

**3. ForexFactory Site Changes**
```bash
# If CSV button location changes, update selectors in the script
# The script tries multiple selector patterns automatically
```

**4. Permission Issues**
```bash
# Run as administrator if file access issues occur
# Or change output directory to a folder you own
```

### 📋 **Verification Steps**

**1. Test Download**
```bash
python ff_auto_downloader.py --run-once
```
Should output: `Success! Processed calendar saved to: [filepath]`

**2. Check Output File**
Open the generated CSV - should contain:
- Economic events (High/Medium only)
- Anticipation events (e.g., "2H Before NFP Anticipation")
- Market opens (e.g., "London Market Open")
- Strategy IDs (e.g., "21102")

**3. Check Logs**
Look at `calendar_downloader.log` for detailed process information.

## Advanced Features

### 🚀 **Additional Capabilities**

**1. Error Recovery**
- Automatic retry logic for failed downloads
- Graceful handling of ForexFactory site changes
- Comprehensive logging for debugging

**2. Data Validation**
- Validates downloaded CSV format
- Checks for missing critical columns
- Filters invalid date/time entries

**3. Archive Management**
- Automatically archives original downloads
- Prevents duplicate processing
- Maintains audit trail

**4. Performance Optimization**
- Efficient pandas processing
- Minimal memory usage
- Fast CSV generation

## Next Steps

1. **Test the system** with `--run-once` 
2. **Verify output quality** matches your requirements
3. **Schedule automatic runs** for Sunday 12 PM
4. **Integrate with your existing MT4 pipeline**
5. **Monitor logs** for any issues

The system is designed to be a **drop-in replacement** for manual ForexFactory downloads while adding all your sophisticated processing automatically.
