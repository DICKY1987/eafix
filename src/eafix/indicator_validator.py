from __future__ import annotations
from typing import Dict, Any
from .indicator_status import IndicatorStatus

HARD_RISK_CAP = 3.5  # percent

class IndicatorValidator:
    """Validation helpers for indicator parameters and matrix combos."""

    @staticmethod
    def clamp_risk_percent(risk: float) -> float:
        try:
            r = float(risk)
        except Exception as exc:
            raise ValueError(f"risk percent must be numeric: {risk!r}") from exc
        if r < 0:
            r = 0.0
        if r > HARD_RISK_CAP:
            r = HARD_RISK_CAP
        return round(r, 4)

    @staticmethod
    def validate_param_set(params: Dict[str, Any]) -> Dict[str, Any]:
        """Defense-in-depth: enforce caps and sane bounds across a generated param set."""
        out = dict(params or {})
        # Risk
        rp = out.get("global_risk_percent", 0)
        out["global_risk_percent"] = IndicatorValidator.clamp_risk_percent(rp)

        # Optional SL/TP/ATR constraints if present
        if "atr_multiplier" in out:
            am = float(out["atr_multiplier"])
            if am <= 0:
                raise ValueError("atr_multiplier must be > 0")
        if "sl_pct" in out:
            sp = float(out["sl_pct"])
            if sp <= 0:
                raise ValueError("sl_pct must be > 0")
        if "tp_pct" in out:
            tp = float(out["tp_pct"])
            if tp <= 0:
                raise ValueError("tp_pct must be > 0")
        # Window minutes if present should be positive ints
        if "window_minutes" in out:
            wm = int(out["window_minutes"])
            if wm <= 0:
                raise ValueError("window_minutes must be > 0")
            out["window_minutes"] = wm
        return out

    @staticmethod
    def validate_combo_fields(combo: Dict[str, Any]) -> None:
        required = ["symbol", "indicator_key", "status", "bias", "duration", "proximity", "context"]
        for k in required:
            if k not in combo:
                raise ValueError(f"combo missing required field: {k}")
        # Status must be canonical and use full TEST (not TES)
        IndicatorStatus.from_string(combo["status"])
        # Context must include window tag for indicator-driven signals when relevant
        ctx = str(combo.get("context", ""))
        if ctx and ctx.startswith("CTX:W") and not ctx[5:].isdigit():
            raise ValueError("context window tag must look like CTX:W15 (minutes)")
