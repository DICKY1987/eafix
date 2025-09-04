from __future__ import annotations
from . import loaders
from apf_core.models import ProcessFlow

def export_yaml(flow: ProcessFlow) -> str:
    # Use the same normalized dumping as loaders
    return loaders.dump_yaml_flow(flow)
