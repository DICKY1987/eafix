from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from .stepkey import StepKey, next_key, midpoint_key

class StepSequencer:
    """
    Handles inserting and renumbering steps using decimal StepKey strategy.
    """

    def insert_after(self, ids: List[str], after: str, new_id_hint: Optional[str] = None) -> str:
        """
        Compute a new StepKey to insert after `after` within ordered list `ids`.
        Returns the string StepKey.
        """
        skeys = [StepKey.parse(x) for x in ids]
        if after not in ids:
            raise ValueError(f"after key {after!r} not found")
        i = ids.index(after)
        a = StepKey.parse(after)
        if i + 1 < len(ids):
            b = StepKey.parse(ids[i + 1])
            newk = midpoint_key(a, b)
        else:
            newk = next_key(a)
        return str(newk)

    def renumber(self, ids: List[str], start: str = "1.001", increment: str = "0.001") -> List[str]:
        """
        Return a new ordered id list renumbered from `start` by `increment`.
        """
        cur = StepKey.parse(start)
        inc = Decimal(increment)
        out = []
        for _ in ids:
            out.append(str(cur))
            cur = next_key(cur, inc)
        return out
