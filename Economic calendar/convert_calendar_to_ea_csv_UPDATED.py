import pandas as pd
from datetime import datetime, timedelta

# Load ForexFactory raw data (adjusted format)
raw_path = "ff_calendar_raw.csv"  # Input file
output_path = "ea_events.csv"      # Output file

# Read raw data
df = pd.read_csv(raw_path)

# Fix Date and Time to correct formats
# Merge Date and Time, and fix 12h -> 24h time conversion
df['EventTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%m-%d-%Y %I:%M%p', errors='coerce')

# Filter: remove holidays, low-impact, CHF events, and weekend issues
df = df[~df['Impact'].str.contains("Holiday|Low", na=False)]
df = df[~df['Country'].str.contains("CHF", na=False)]
df = df[df['EventTime'].dt.dayofweek < 5]  # Monday to Friday only
df = df[~((df['EventTime'].dt.dayofweek == 4) & (df['EventTime'].dt.hour >= 15))]  # Friday after 15:00
df = df[~((df['EventTime'].dt.dayofweek == 6) & (df['EventTime'].dt.hour < 18))]   # Sunday before 18:00

# Create EA-compatible fields
df['id'] = df['EventTime'].dt.strftime('%Y%m%d%H%M') + '_' + df['Country']
df['symbol'] = df['Country'] + 'USD'  # Assuming all symbols end with USD (can improve later)
df['eventName'] = df['Title']
df['eventType'] = 'Event'
df['impact'] = df['Impact']
df['tradeEnabled'] = 'true'
df['entryTimeStr'] = df['EventTime'].dt.strftime('%Y.%m.%d %H:%M')
df['offset'] = 0
df['entryType'] = 'Event'

# SL/TP based on impact
df['slPips'] = 15
df['tpPips'] = 30
df.loc[df['Impact'].str.contains("High", na=False), 'slPips'] = 20
df.loc[df['Impact'].str.contains("High", na=False), 'tpPips'] = 40

# Buffer settings
df['bufferPips'] = 10

# Trailing and Pending trail settings
df['trailingType'] = 'step'
df.loc[df['Impact'].str.contains("High", na=False), 'trailingType'] = 'percent'

df['pendingTrail'] = 'false'
df.loc[df['Impact'].str.contains("High", na=False), 'pendingTrail'] = 'true'

# Lot sizing and partial close
df['lotInput'] = 'AUTO'
df['partialCloseEnabled'] = 'true'
df['partialCloseTriggerPips'] = 10
df['partialClosePercent'] = 50

# Execution window
df['winStartStr'] = (df['EventTime'] - timedelta(minutes=5)).dt.strftime('%Y.%m.%d %H:%M')
df['winEndStr'] = (df['EventTime'] + timedelta(minutes=5)).dt.strftime('%Y.%m.%d %H:%M')

# Misc fields
df['rawEventTime'] = df['entryTimeStr']
df['magicNumber'] = 0
df['strategy'] = 'straddle'
df['forceShutdownAfterTrade'] = 'false'
df['notes'] = df['Title'] + ' | Impact: ' + df['Impact']
df['genTimestamp'] = datetime.now().strftime('%Y.%m.%d %H:%M')

# Final export columns
columns = ['id','symbol','eventName','eventType','impact','tradeEnabled','entryTimeStr','offset',
           'entryType','slPips','tpPips','bufferPips','trailingType','pendingTrail','lotInput',
           'partialCloseEnabled','partialCloseTriggerPips','partialClosePercent',
           'winStartStr','winEndStr','rawEventTime','magicNumber','strategy','forceShutdownAfterTrade','notes','genTimestamp']

# Save to output file
df[columns].to_csv(output_path, index=False, sep=';')
print(f"EA-compatible file saved to: {output_path}")