import numpy as np
import pandas as pd

def robust_zscore(s: pd.Series, win: int = 52):
    m = s.rolling(win, min_periods=int(win*0.6)).median()
    mad = (s - m).abs().rolling(win, min_periods=int(win*0.6)).median()
    z = (s - m) / (1.4826 * mad.replace(0, np.nan))
    return z.clip(-8, 8)

def make_institutional_features(cot_df: pd.DataFrame, resample_freq: str):
    # Input: columns = ['report_date','pair','inst_net_ratio']
    if cot_df.empty:
        return pd.DataFrame()
    cot_p = cot_df.pivot(index="report_date", columns="pair", values="inst_net_ratio").sort_index()
    # Weekly to target freq via ffill
    cot_p = cot_p.asfreq("W-FRI").ffill()
    if resample_freq.upper() != "W":
        cot_p = cot_p.resample(resample_freq).ffill()
    # Z-scores per pair
    feats = {}
    for col in cot_p.columns:
        s = cot_p[col]
        feats[f"{col}_inst_net_ratio"] = s
        feats[f"{col}_inst_net_ratio_z"] = robust_zscore(s)
    out = pd.DataFrame(feats, index=cot_p.index)
    return out

def make_retail_features(retail_df: pd.DataFrame, pair: str, resample_freq: str):
    # retail_df columns: timestamp(optional), pct_long, pct_short, ls_ratio
    if retail_df.empty:
        return pd.DataFrame()
    retail_df = retail_df.copy()
    if "timestamp" in retail_df.columns:
        retail_df["timestamp"] = pd.to_datetime(retail_df["timestamp"])
        retail_df = retail_df.set_index("timestamp")
    else:
        # If no timestamp, create a dummy range index
        retail_df.index = pd.date_range(start=pd.Timestamp.utcnow(), periods=len(retail_df), freq="T")
    retail_df = retail_df.resample(resample_freq).mean()
    out = pd.DataFrame({
        f"{pair}_retail_pct_long": retail_df["pct_long"],
        f"{pair}_retail_pct_short": retail_df["pct_short"],
        f"{pair}_retail_ls_ratio": retail_df["ls_ratio"],
        f"{pair}_retail_ls_ratio_z": robust_zscore(retail_df["ls_ratio"])
    }, index=retail_df.index)
    return out

def combine_inst_retail(inst_df: pd.DataFrame, retail_df: pd.DataFrame, pair: str):
    # Align and build divergence feature
    df = inst_df.join(retail_df, how="outer").sort_index().ffill()
    a = df.get(f"{pair}_inst_net_ratio_z")
    b = df.get(f"{pair}_retail_ls_ratio_z")
    if a is None or b is None:
        return df
    df[f"{pair}_positioning_divergence"] = a - b
    return df

def shift_features(df: pd.DataFrame, n: int = 1):
    return df.shift(n)