from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class IndicatorStatus(str, Enum):
    EXPERIMENTAL = "EXP"
    VALIDATION = "VAL"
    TEST = "TEST"
    PRODUCTION = "PROD"

    @classmethod
    def from_string(cls, s: str) -> "IndicatorStatus":
        s = (s or "").strip().upper()
        mapping = {
            "EXP": cls.EXPERIMENTAL, "EXPERIMENTAL": cls.EXPERIMENTAL,
            "VAL": cls.VALIDATION, "VALIDATION": cls.VALIDATION,
            "TEST": cls.TEST, "TES": cls.TEST,
            "PROD": cls.PRODUCTION, "PRODUCTION": cls.PRODUCTION,
        }
        if s not in mapping:
            raise ValueError(f"Unknown IndicatorStatus: {s!r}")
        return mapping[s]

    @property
    def prefix(self) -> str:
        # Use full TEST, not TES
        return str(self.value)

def format_indicator_key(status: IndicatorStatus, name: str) -> str:
    """Format a canonical indicator key, e.g., TEST_RSI_DIVERGENCE"""
    if not name or not name.strip():
        raise ValueError("Indicator name cannot be empty")
    clean = name.strip().upper().replace(" ", "_")
    return f"{status.prefix}_{clean}"
