
import pandas as pd
from datetime import datetime, timedelta

# Load raw ForexFactory calendar data (CSV format)
raw_path = "ff_calendar_raw.csv"
output_path = "ea_events.csv"

# Read raw data - you may need to adjust based on the format from ForexFactory
df = pd.read_csv(raw_path)

# Filter: remove low-impact, CHF events, and Fri 15:00 CST to Sun 18:00 CST
df = df[~df['Impact'].str.contains("Low", na=False)]
df = df[~df['Currency'].str.contains("CHF", na=False)]

# Convert Date and Time columns to datetime
df['EventTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce')

# Remove weekend events
df = df[df['EventTime'].dt.dayofweek < 5]  # Monday to Friday only
df = df[~((df['EventTime'].dt.dayofweek == 4) & (df['EventTime'].dt.hour >= 15))]  # Friday after 15:00
df = df[~((df['EventTime'].dt.dayofweek == 6) & (df['EventTime'].dt.hour < 18))]   # Sunday before 18:00

# Create EA-compatible fields
df['id'] = df['EventTime'].dt.strftime('%Y%m%d%H%M') + '_' + df['Currency']
df['symbol'] = df['Currency'] + 'USD'  # Simplified pairing
df['eventName'] = df['Event']
df['eventType'] = 'Event'
df['impact'] = df['Impact']
df['tradeEnabled'] = 'true'
df['entryTimeStr'] = df['EventTime'].dt.strftime('%Y.%m.%d %H:%M')
df['offset'] = 0
df['entryType'] = 'Event'
df['slPips'] = 15
df['tpPips'] = 30
df['bufferPips'] = 10
df['trailingType'] = 'step'
df['lotInput'] = 'AUTO'
df['winStartStr'] = (df['EventTime'] - timedelta(minutes=5)).dt.strftime('%Y.%m.%d %H:%M')
df['winEndStr'] = (df['EventTime'] + timedelta(minutes=5)).dt.strftime('%Y.%m.%d %H:%M')
df['rawEventTime'] = df['entryTimeStr']
df['magicNumber'] = 0
df['strategy'] = 'straddle'
df['notes'] = df['eventName']
df['genTimestamp'] = datetime.now().strftime('%Y.%m.%d %H:%M')

# Final columns for EA
columns = ['id','symbol','eventName','eventType','impact','tradeEnabled','entryTimeStr','offset',
           'entryType','slPips','tpPips','bufferPips','trailingType','lotInput',
           'winStartStr','winEndStr','rawEventTime','magicNumber','strategy','notes','genTimestamp']

# Export to CSV
df[columns].to_csv(output_path, index=False, sep=';')
print(f"EA-compatible file saved to: {output_path}")
