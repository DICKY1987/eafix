"""
JSON importer for process flows.
"""
import json
from ....core.models.process_flow import ProcessFlow

def import_json(file_path: str) -> ProcessFlow:
    """Import a process flow from a JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    # TODO: Convert data to ProcessFlow instance
    return data
