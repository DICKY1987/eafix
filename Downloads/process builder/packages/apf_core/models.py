from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

@dataclass
class Step:
    id: str
    actor: str
    action: str
    text: str
    next: Optional[List[str]] = field(default_factory=list)

@dataclass
class ProcessFlow:
    meta: Dict[str, str]
    steps: List[Step]

    def step_index(self) -> Dict[str, Step]:
        return {s.id: s for s in self.steps}
