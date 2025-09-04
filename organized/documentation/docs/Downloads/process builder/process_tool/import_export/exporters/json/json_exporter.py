"""
JSON exporter for process flows.
"""
import json

def export_json(process_flow, file_path):
    """Export a process flow to a JSON file (stub)."""
    # TODO: Convert process_flow to dict
    with open(file_path, 'w') as f:
        json.dump({}, f)
