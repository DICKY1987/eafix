from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, getcontext

getcontext().prec = 28

@dataclass(frozen=True, order=True)
class StepKey:
    """
    Decimal StepKey with optional thousandth precision: e.g., 1.000, 1.0015
    Internally stores as Decimal to support midpoints.
    """
    major: int
    minor: Decimal  # thousandths (or arbitrary fractional precision)

    @classmethod
    def parse(cls, s: str) -> "StepKey":
        if "." in s:
            major_str, frac_str = s.split(".", 1)
            major = int(major_str)
            minor = Decimal("0." + frac_str)
        else:
            major = int(s)
            minor = Decimal("0")
        return cls(major, minor)

    def __str__(self) -> str:
        # Keep as minimal fractional digits necessary but at least 3 if non-zero thousandths present
        if self.minor == 0:
            return f"{self.major}"
        # Represent fractional without leading "0."
        frac = str(self.minor).split(".", 1)[1].rstrip("0")
        # default to 3 if shorter
        if len(frac) < 3:
            frac = (frac + "000")[:3]
        return f"{self.major}.{frac}"

    def to_decimal(self) -> Decimal:
        return Decimal(self.major) + self.minor

def midpoint_key(a: "StepKey", b: "StepKey") -> "StepKey":
    """
    Return a midpoint StepKey strictly between a and b.
    """
    da, db = a.to_decimal(), b.to_decimal()
    mid = (da + db) / 2
    major = int(mid)
    minor = mid - major
    return StepKey(major, minor)

def next_key(a: "StepKey", increment: Decimal = Decimal("0.001")) -> "StepKey":
    d = a.to_decimal() + increment
    major = int(d)
    minor = d - major
    return StepKey(major, minor)
