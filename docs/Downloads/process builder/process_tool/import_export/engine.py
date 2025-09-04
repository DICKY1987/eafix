def import_process(file_path, format):
def export_process(process_flow, file_path, format):
"""
Import/export engine for process files.
Handles registration and dispatch to importers/exporters.
"""
from .importers.yaml_importer import import_yaml
from .importers.prose_importer import import_prose
from .importers.json.json_importer import import_json
from .exporters.yaml_exporter import export_yaml
from .exporters.markdown_exporter import export_markdown
from .exporters.drawio_exporter import export_drawio
from .exporters.json.json_exporter import export_json

def import_process(file_path, format):
    """Import a process from the given file and format."""
    if format == "yaml":
        return import_yaml(file_path)
    elif format == "prose":
        return import_prose(file_path)
    elif format == "json":
        return import_json(file_path)
    else:
        raise ValueError(f"Unsupported import format: {format}")

def export_process(process_flow, file_path, format):
    """Export a process flow to the given file and format."""
    if format == "yaml":
        return export_yaml(process_flow, file_path)
    elif format == "markdown":
        return export_markdown(process_flow, file_path)
    elif format == "drawio":
        return export_drawio(process_flow, file_path)
    elif format == "json":
        return export_json(process_flow, file_path)
    else:
        raise ValueError(f"Unsupported export format: {format}")
