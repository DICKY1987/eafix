"""
ProcessFlow and ProcessSection models for the Atomic Process Framework.
"""
from typing import List, Optional
from .process_step import ProcessStep, SubProcess, SubProcessCall
from .metadata import ProcessMetadata

class ProcessSection:
    """
    Represents a major section of a process (e.g., Initialization, Processing).
    """
    def __init__(self, name: str, steps: Optional[List[ProcessStep]] = None):
        self.name = name
        self.steps = steps or []

class ProcessFlow:
    """
    Container for complete process documentation, including metadata and sections.
    """
    def __init__(self, metadata: Optional[ProcessMetadata] = None, sections: Optional[List[ProcessSection]] = None):
        self.metadata = metadata
        self.sections = sections or []
