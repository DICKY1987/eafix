"""Calendar Data Management component placeholder."""
from dataclasses import dataclass


@dataclass
class DataManagement:
    """Placeholder for file upload/import status widgets."""
    imported_rows: int = 0

    def record_import(self, rows: int) -> None:
        """Record number of imported rows."""
        self.imported_rows = rows
