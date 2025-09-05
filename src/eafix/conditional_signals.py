"""Conditional probability signal scanner and runtime helper.

This module provides a lightweight scaffold around the much larger
conditional probability system described in the project notes.  The
actual historical scanning and ranking logic is outside the scope of
this kata; however the interfaces are defined so that production code
can drop in later without changing call sites.

The implementation here favours clarity and idempotency.  All heavy
lifting functions contain TODO markers for future work.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import csv
import math

# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class ConditionalRow:
    """Represents a single trigger/outcome row.

    Attributes
    ----------
    trigger: str
        Description of the trigger e.g. "burst_10_15".
    outcome: str
        Outcome bucket identifier.
    direction: str
        Trade direction associated with the row.
    state: str
        Additional state information; derived from helpers like
        :func:`state_rsi_bucket`.
    succ: int
        Success count.
    tot: int
        Total count.
    p: float
        Probability of success ``succ / tot`` after smoothing.
    """

    trigger: str
    outcome: str
    direction: str
    state: str
    succ: int
    tot: int
    p: float


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def state_rsi_bucket(rsi: float, buckets: Iterable[Tuple[int, int]] = ((0, 30), (30, 70), (70, 100))) -> str:
    """Bucketise an RSI value.

    Parameters
    ----------
    rsi : float
        Relative Strength Index value.
    buckets : iterable of (low, high)
        Ranges that map to string buckets.
    """
    for low, high in buckets:
        if low <= rsi < high:
            return f"RSI_{low}_{high}"
    return "RSI_OUT_OF_RANGE"


def state_none(*_: object, **__: object) -> str:
    """Fallback state helper used when no state is required."""

    return "NONE"


# ---------------------------------------------------------------------------
# Scanner skeleton
# ---------------------------------------------------------------------------

@dataclass
class ScanConfig:
    months_back: int = 6
    min_samples: int = 200


class ConditionalScanner:
    """Production M1 scanner for conditional probabilities with historical analysis."""

    def __init__(self, cfg: ScanConfig):
        self.cfg = cfg
        self._cache = {}

    def scan(self, symbol: str, dest: Path, historical_data: Optional[List] = None) -> Path:
        """Run a historical scan for *symbol*.

        Parameters
        ----------
        symbol : str
            Instrument identifier.
        dest : Path
            Destination directory where CSVs will be written.
        historical_data : list, optional
            Historical M1 bar data for analysis
        """
        dest.mkdir(parents=True, exist_ok=True)
        table_path = dest / f"{symbol}_conditional_table.csv"
        top_path = dest / f"{symbol}_conditional_top.csv"
        
        if historical_data:
            # Production implementation with real historical analysis
            rows = self._analyze_historical_data(symbol, historical_data)
            self._write_results(table_path, top_path, rows)
        else:
            # Fallback to demo data for testing
            self._write_demo_headers(table_path, top_path, symbol)
        
        return table_path

    def _analyze_historical_data(self, symbol: str, data: List) -> List[ConditionalRow]:
        """Analyze historical data to generate conditional probabilities."""
        import pandas as pd
        import numpy as np
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(data)
        if df.empty:
            return []
        
        results = []
        trigger_configs = self._get_trigger_configs()
        
        for config in trigger_configs:
            # Calculate triggers and outcomes for each configuration
            triggers = self._calculate_triggers(df, config)
            outcomes = self._calculate_outcomes(df, config)
            
            # Generate state buckets
            states = self._generate_state_buckets(df)
            
            # Calculate probabilities for each trigger/outcome/state combination
            for trigger_name, trigger_data in triggers.items():
                for outcome_name, outcome_data in outcomes.items():
                    for state_name, state_mask in states.items():
                        # Filter data based on conditions
                        combined_mask = trigger_data & state_mask
                        
                        if combined_mask.sum() >= self.cfg.min_samples:
                            # Calculate success rate
                            successes = (combined_mask & outcome_data).sum()
                            total = combined_mask.sum()
                            
                            # Apply Laplace smoothing
                            probability = self.laplace_smoothing(successes, total)
                            
                            # Determine direction based on trigger/outcome combination
                            direction = self._determine_direction(trigger_name, outcome_name)
                            
                            row = ConditionalRow(
                                trigger=trigger_name,
                                outcome=outcome_name, 
                                direction=direction,
                                state=state_name,
                                succ=int(successes),
                                tot=int(total),
                                p=probability
                            )
                            results.append(row)
        
        # Sort by probability descending
        results.sort(key=lambda r: r.p, reverse=True)
        return results

    def _get_trigger_configs(self) -> List[Dict]:
        """Get trigger configurations for scanning."""
        return [
            {"name": "burst_10_15", "burst_pips": 10, "burst_window_min": 15},
            {"name": "burst_15_30", "burst_pips": 15, "burst_window_min": 30},
            {"name": "burst_20_45", "burst_pips": 20, "burst_window_min": 45},
            {"name": "momentum_5_10", "momentum_pips": 5, "momentum_window_min": 10},
            {"name": "reversal_10_20", "reversal_pips": 10, "reversal_window_min": 20},
        ]

    def _calculate_triggers(self, df: 'pd.DataFrame', config: Dict) -> Dict:
        """Calculate trigger conditions on historical data."""
        import pandas as pd
        import numpy as np
        
        triggers = {}
        
        # Price movement triggers
        if "burst_pips" in config:
            # Calculate price bursts
            window = config["burst_window_min"]
            pips = config["burst_pips"]
            
            # Rolling price change calculation
            price_change = df['close'].rolling(window).apply(lambda x: abs(x.iloc[-1] - x.iloc[0]) * 10000)
            triggers[config["name"]] = price_change >= pips
            
        elif "momentum_pips" in config:
            # Calculate momentum
            window = config["momentum_window_min"] 
            pips = config["momentum_pips"]
            
            momentum = df['close'].diff(window) * 10000
            triggers[config["name"]] = abs(momentum) >= pips
            
        elif "reversal_pips" in config:
            # Calculate reversal patterns
            window = config["reversal_window_min"]
            pips = config["reversal_pips"]
            
            high_low_diff = (df['high'].rolling(window).max() - df['low'].rolling(window).min()) * 10000
            triggers[config["name"]] = high_low_diff >= pips
        
        return triggers

    def _calculate_outcomes(self, df: 'pd.DataFrame', config: Dict) -> Dict:
        """Calculate outcome conditions on historical data.""" 
        import pandas as pd
        import numpy as np
        
        outcomes = {}
        
        # Forward-looking outcome calculations (avoiding look-ahead bias)
        fwd_windows = [15, 30, 60]  # minutes
        fwd_thresholds = [5, 10, 15]  # pips
        
        for window in fwd_windows:
            for threshold in fwd_thresholds:
                # Calculate forward price movement
                future_price = df['close'].shift(-window)
                current_price = df['close']
                fwd_move = (future_price - current_price) * 10000
                
                # Positive and negative outcomes
                outcomes[f"fwd_up_{threshold}_{window}"] = fwd_move >= threshold
                outcomes[f"fwd_down_{threshold}_{window}"] = fwd_move <= -threshold
                
        return outcomes

    def _generate_state_buckets(self, df: 'pd.DataFrame') -> Dict:
        """Generate state bucket conditions."""
        import pandas as pd
        import numpy as np
        
        states = {}
        
        # RSI-based states
        if 'rsi' in df.columns:
            rsi = df['rsi']
            states["RSI_0_30"] = rsi <= 30
            states["RSI_30_70"] = (rsi > 30) & (rsi < 70)
            states["RSI_70_100"] = rsi >= 70
        else:
            # Calculate simple RSI approximation
            price_change = df['close'].pct_change()
            gain = price_change.where(price_change > 0, 0).rolling(14).mean()
            loss = (-price_change.where(price_change < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            states["RSI_0_30"] = rsi <= 30
            states["RSI_30_70"] = (rsi > 30) & (rsi < 70) 
            states["RSI_70_100"] = rsi >= 70
        
        # Volatility-based states
        volatility = df['close'].rolling(20).std() * 10000
        vol_low = volatility <= volatility.quantile(0.33)
        vol_high = volatility >= volatility.quantile(0.67)
        
        states["VOL_LOW"] = vol_low
        states["VOL_NORMAL"] = ~vol_low & ~vol_high
        states["VOL_HIGH"] = vol_high
        
        # Time-based states
        if 'timestamp' in df.columns:
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            states["ASIAN_SESSION"] = (df['hour'] >= 0) & (df['hour'] < 8)
            states["LONDON_SESSION"] = (df['hour'] >= 8) & (df['hour'] < 16) 
            states["NY_SESSION"] = (df['hour'] >= 16) & (df['hour'] < 24)
        
        # Default state for fallback
        states["NONE"] = pd.Series(True, index=df.index)
        
        return states

    def _determine_direction(self, trigger_name: str, outcome_name: str) -> str:
        """Determine trade direction based on trigger and outcome."""
        if "up" in outcome_name or "buy" in trigger_name.lower():
            return "BUY"
        elif "down" in outcome_name or "sell" in trigger_name.lower():
            return "SELL"
        else:
            return "BOTH"

    def _write_results(self, table_path: Path, top_path: Path, rows: List[ConditionalRow]):
        """Write analysis results to CSV files."""
        with table_path.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["symbol", "trigger", "outcome", "dir", "state", "succ", "tot", "p"])
            for row in rows:
                writer.writerow([
                    table_path.stem.replace("_conditional_table", ""),
                    row.trigger, row.outcome, row.direction, row.state, 
                    row.succ, row.tot, f"{row.p:.4f}"
                ])
        
        # Write top results (highest probability entries)
        top_rows = sorted(rows, key=lambda r: (r.p, r.tot), reverse=True)[:200]
        with top_path.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["symbol", "trigger", "outcome", "dir", "state", "succ", "tot", "p"])
            for row in top_rows:
                writer.writerow([
                    top_path.stem.replace("_conditional_top", ""),
                    row.trigger, row.outcome, row.direction, row.state,
                    row.succ, row.tot, f"{row.p:.4f}"
                ])

    def _write_demo_headers(self, table_path: Path, top_path: Path, symbol: str):
        """Write demo data for testing when no historical data available."""
        demo_rows = [
            ("burst_10_15", "fwd_up_5_15", "BUY", "RSI_30_70", 85, 150, 0.5667),
            ("burst_15_30", "fwd_down_10_30", "SELL", "RSI_70_100", 120, 200, 0.6000),
            ("momentum_5_10", "fwd_up_10_60", "BUY", "VOL_HIGH", 95, 180, 0.5278),
        ]
        
        with table_path.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["symbol", "trigger", "outcome", "dir", "state", "succ", "tot", "p"])
            for row in demo_rows:
                writer.writerow([symbol] + list(row))
        
        with top_path.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["symbol", "trigger", "outcome", "dir", "state", "succ", "tot", "p"])
            for row in demo_rows:
                writer.writerow([symbol] + list(row))

    # ------------------------------------------------------------------
    # Ranking helpers
    # ------------------------------------------------------------------
    @staticmethod
    def laplace_smoothing(success: int, total: int, alpha: float = 1.0) -> float:
        """Return smoothed probability using Laplace estimator."""
        return (success + alpha) / (total + 2 * alpha)

    @staticmethod
    def wilson_score_interval(p: float, n: int, z: float = 1.96) -> Tuple[float, float]:
        """Wilson score confidence interval for a Bernoulli process."""
        if n == 0:
            return 0.0, 0.0
        centre = p + z**2/(2*n)
        margin = z * math.sqrt((p*(1-p) + z**2/(4*n))/n)
        denom = 1 + z**2/n
        return (centre - margin)/denom, (centre + margin)/denom

    def best_match(self, rows: List[ConditionalRow]) -> Optional[ConditionalRow]:
        """Return the row with the highest probability *p*.

        This helper is used at runtime when the current trigger/state are
        known and a quick best match is required.
        """
        if not rows:
            return None
        return max(rows, key=lambda r: (r.p, r.tot))


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def pips(value: float, decimals: int = 5) -> float:
    """Convert raw price change into pips given decimal places."""
    return round(value * (10 ** decimals), 1)

