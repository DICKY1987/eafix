import io
import zipfile
import requests
import pandas as pd
from datetime import datetime

# Mapping CFTC futures tickers to FX pairs
CFTC_TO_PAIR = {
    # CFTC 'Market and Exchange Names' (Disaggregated Futures Only)
    # Adjust if your downloaded report uses different naming
    "EURO FX - CHICAGO MERCANTILE EXCHANGE": "EURUSD",
    "JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE": "USDJPY",
    "BRITISH POUND STERLING - CHICAGO MERCANTILE EXCHANGE": "GBPUSD",
    "SWISS FRANC - CHICAGO MERCANTILE EXCHANGE": "USDCHF",
    "AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE": "AUDUSD",
    "CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE": "USDCAD",
    "NEW ZEALAND DOLLAR - CHICAGO MERCANTILE EXCHANGE": "NZDUSD",
}

def _fetch_cftc_disagg_csv() -> pd.DataFrame:
    # CFTC publishes weekly disaggregated CSV (futures only).
    # URL is intentionally parameterized in case CFTC rotates paths.
    url = "https://www.cftc.gov/dea/newcot/FinFutWk.txt"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    # This is a '|' delimited text with header
    df = pd.read_csv(io.StringIO(r.text), sep=",|\t|\|", engine="python")
    return df

def _fetch_cftc_legacy_csv() -> pd.DataFrame:
    # Legacy 'futures only' weekly report
    url = "https://www.cftc.gov/dea/newcot/f_disagg.txt"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text), sep=",|\t|\|", engine="python")
    return df

def get_cot_disaggregated() -> pd.DataFrame:
    df = _fetch_cftc_disagg_csv()
    # Normalize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    # Expect 'market_and_exchange_names', 'report_date_as_yyyy-mm-dd', positions...
    df["report_date"] = pd.to_datetime(df["report_date_as_yyyy-mm-dd"])
    # Filter to currencies in our map
    df = df[df["market_and_exchange_names"].isin(CFTC_TO_PAIR.keys())].copy()
    df["pair"] = df["market_and_exchange_names"].map(CFTC_TO_PAIR)
    # Compute institutional net ratio ~ non-commercials proxy
    # Try to use 'money_manager' category if available, fallback to 'noncommercials'
    long_cols = [c for c in df.columns if "money_manager_longs" in c or "noncommercial_long" in c]
    short_cols = [c for c in df.columns if "money_manager_shorts" in c or "noncommercial_short" in c]
    oi_cols = [c for c in df.columns if "open_interest" in c and "change" not in c]
    long_col = long_cols[0] if long_cols else None
    short_col = short_cols[0] if short_cols else None
    oi_col = oi_cols[0] if oi_cols else None
    if not all([long_col, short_col, oi_col]):
        raise RuntimeError("CFTC schema changed; update column mappings.")

    df["inst_net_ratio"] = (df[long_col] - df[short_col]) / df[oi_col].replace(0, pd.NA)
    out = df[["report_date", "pair", "inst_net_ratio"]].dropna()
    return out

def get_cot_legacy() -> pd.DataFrame:
    df = _fetch_cftc_legacy_csv()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    # Map legacy names if needed (left as an exercise; prefer disaggregated above)
    raise NotImplementedError("Legacy parser not implemented; use disaggregated.")