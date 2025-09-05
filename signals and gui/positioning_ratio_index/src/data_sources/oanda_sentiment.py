import time
import pandas as pd
import requests

# Minimal OANDA v20 PositionBook pull (requires token).
# Docs: https://developer.oanda.com/rest-live-v20/instrument-ep/

def fetch_oanda_positionbook(instrument: str, token: str, account_type: str = "practice"):
    base = "https://api-fxpractice.oanda.com" if account_type == "practice" else "https://api-fxtrade.oanda.com"
    url = f"{base}/v3/instruments/{instrument}/positionBook"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code != 200:
        raise RuntimeError(f"OANDA error {r.status_code}: {r.text}")
    data = r.json()
    # PositionBook provides buckets; compute %long/%short from longs/shorts totals
    buckets = data.get("positionBook", {}).get("buckets", [])
    if not buckets:
        return None
    df = pd.DataFrame(buckets)
    # longs & shorts are strings; convert
    df["longCountPercent"] = pd.to_numeric(df["longCountPercent"])
    df["shortCountPercent"] = pd.to_numeric(df["shortCountPercent"])
    # Aggregate to top-level ratio
    pct_long = df["longCountPercent"].mean()
    pct_short = df["shortCountPercent"].mean()
    out = pd.DataFrame({"pct_long":[pct_long], "pct_short":[pct_short]})
    return out

def long_short_ratio(row):
    # Convert % to ratio Long/Short
    if row["pct_short"] == 0:
        return None
    return (row["pct_long"]) / (row["pct_short"])

def get_oanda_sentiment_series(instrument: str, token: str, n_samples: int = 1, sleep_sec: int = 1, account_type: str = "practice"):
    # Pull N samples (crude polling). For intraday, schedule in cron or APScheduler.
    rows = []
    for _ in range(n_samples):
        try:
            snap = fetch_oanda_positionbook(instrument, token, account_type)
            if snap is not None:
                rows.append(snap.iloc[0].to_dict())
        except Exception as e:
            pass
        time.sleep(sleep_sec)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["ls_ratio"] = df.apply(long_short_ratio, axis=1)
    return df