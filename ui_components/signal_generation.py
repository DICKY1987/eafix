"""Signal generation component placeholder."""
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class SignalGeneration:
    """Stores generated signals."""
    signals: List[Dict[str, str]] = None

    def record(self, signal: Dict[str, str]) -> None:
        if self.signals is None:
            self.signals = []
        self.signals.append(signal)
