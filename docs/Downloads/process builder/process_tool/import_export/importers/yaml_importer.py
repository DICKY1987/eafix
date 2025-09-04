def import_yaml(file_path):
"""
YAML file importer for process flows.
"""
import yaml
from ...core.models.process_flow import ProcessFlow

def import_yaml(file_path: str) -> ProcessFlow:
    """Import a process flow from a YAML file."""
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    # TODO: Convert data to ProcessFlow instance
    return data
