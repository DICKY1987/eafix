"""
Process metadata models for the Atomic Process Framework.
"""
from typing import Optional

class ProcessMetadata:
    """
    Metadata for a process flow (author, version, timestamps, etc.).
    """
    def __init__(self, author: str, version: str, created: Optional[str] = None, updated: Optional[str] = None, description: Optional[str] = None):
        self.author = author
        self.version = version
        self.created = created
        self.updated = updated
        self.description = description
