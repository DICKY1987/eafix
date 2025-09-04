from __future__ import annotations
import json, os
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Iterable, Optional
from .indicator_status import IndicatorStatus, format_indicator_key
from .indicator_validator import IndicatorValidator

MATRIX_STORE = os.environ.get("MATRIX_STORE", "./dynamic_matrix.json")

@dataclass
class Combo:
    symbol: str
    indicator_key: str
    status: str              # EXP|VAL|TEST|PROD (canonical)
    bias: str                # LONG|SHORT|BOTH|NONE
    duration: str            # FLASH|QUICK|LONG|EXTENDED or NONE
    proximity: str           # NONE for technicals; otherwise event proximity
    context: str             # e.g., CTX:W15 to disambiguate window-based indicators
    params: Dict[str, Any]

class DynamicMatrixManager:
    """Drop-in manager to register indicator-driven combos with explicit context tags.
    For non-event technical indicators, set proximity to "NONE" and duration to "NONE" unless you
    purposely bucket by duration.

    Combos are stored in-memory as :class:`Combo` instances for stronger typing and are
    serialized to dictionaries when persisted to disk or returned from public APIs.
    """

    def __init__(self, storage_path: Optional[str] = None) -> None:
        self.storage_path = storage_path or MATRIX_STORE
        self._combos: List[Combo] = []
        self._load()

    # ---------------- Persistence ----------------
    def _load(self) -> None:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    self._combos = [Combo(**c) for c in raw]
            except Exception:
                self._combos = []
        else:
            self._combos = []

    def _save(self) -> None:
        tmp = self.storage_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump([asdict(c) for c in self._combos], f, indent=2, sort_keys=True)
        os.replace(tmp, self.storage_path)

    # ---------------- API ----------------
    def register_indicator(
        self,
        *, name: str, status: IndicatorStatus, symbols: Iterable[str],
        base_params: Dict[str, Any], windows: Iterable[int]
    ) -> List[Dict[str, Any]]:
        """Register indicator combos for multiple symbols and windows.
        Adds explicit CTX:W{minutes} context and clamps risk via validator.
        """
        indicator_key = format_indicator_key(status, name)
        created: List[Dict[str, Any]] = []
        for sym in symbols:
            for wm in windows:
                params = dict(base_params or {})
                params["window_minutes"] = int(wm)
                params = IndicatorValidator.validate_param_set(params)

                combo = Combo(
                    symbol=sym,
                    indicator_key=indicator_key,
                    status=status.name,  # EXPERIMENTAL, VALIDATION, TEST, PRODUCTION
                    bias=params.get("bias", "BOTH"),
                    duration=params.get("duration", "NONE"),
                    proximity=params.get("proximity", "NONE"),
                    context=f"CTX:W{params['window_minutes']}",
                    params=params,
                )
                IndicatorValidator.validate_combo_fields(asdict(combo))
                self._combos.append(combo)
                created.append(asdict(combo))

        self._save()
        return created

    def list(self) -> List[Dict[str, Any]]:
        return [asdict(c) for c in self._combos]

    def find_by_indicator(self, indicator_key: str) -> List[Dict[str, Any]]:
        indicator_key = (indicator_key or "").upper()
        return [asdict(c) for c in self._combos if c.indicator_key.upper() == indicator_key]

    def delete_by_indicator(self, indicator_key: str) -> int:
        indicator_key = (indicator_key or "").upper()
        before = len(self._combos)
        self._combos = [c for c in self._combos if c.indicator_key.upper() != indicator_key]
        removed = before - len(self._combos)
        if removed:
            self._save()
        return removed
