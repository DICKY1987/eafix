from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Iterable, List
from .indicator_validator import IndicatorValidator

DEFAULT_WINDOWS = [15, 60, 240, 480, 720, 1440]  # 15m, 1h, 4h, 8h, 12h, 24h

@dataclass
class PercentChangeParams:
    window_minutes: int
    global_risk_percent: float = 2.5
    lookback_bars: int = 200
    method: str = "log_return"  # or "simple_return"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "window_minutes": self.window_minutes,
            "global_risk_percent": self.global_risk_percent,
            "lookback_bars": self.lookback_bars,
            "method": self.method,
        }

def generate_percent_change_param_sets(windows: Iterable[int] = None, base_risk: float = 2.5) -> List[Dict[str, Any]]:
    """Generate validated param sets for percent-change indicators across windows.
    Enforces the hard risk cap (3.5%) in the validator.
    """
    windows = list(windows or DEFAULT_WINDOWS)
    out: List[Dict[str, Any]] = []
    for w in windows:
        params = PercentChangeParams(window_minutes=int(w), global_risk_percent=float(base_risk)).as_dict()
        out.append(IndicatorValidator.validate_param_set(params))
    return out
