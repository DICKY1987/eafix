"""Processing engine component placeholder."""
from dataclasses import dataclass


@dataclass
class ProcessingEngine:
    """Tracks pipeline stage counts."""
    raw_count: int = 0
    filtered_count: int = 0
    output_count: int = 0
