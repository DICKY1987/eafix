"""Filtering and Processing component placeholder."""
from dataclasses import dataclass
from typing import Dict


@dataclass
class FilteringProcessing:
    """Stores currency mappings and exclusions."""
    currency_map: Dict[str, str] = None
    exclude_chf: bool = True
