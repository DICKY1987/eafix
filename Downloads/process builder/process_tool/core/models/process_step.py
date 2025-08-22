"""
ProcessStep, SubProcess, and SubProcessCall models for the Atomic Process Framework.
"""
from typing import List, Optional, Dict, Any

class ProcessStep:
    """
    Represents an individual atomic action in a process.
    """
    def __init__(self, step_id: str, actor: str, description: str, dependencies: Optional[List[str]] = None,
                 validation: Optional[List[str]] = None, sla_ms: Optional[int] = None, error_handling: Optional[Dict[str, Any]] = None):
        self.step_id = step_id
        self.actor = actor
        self.description = description
        self.dependencies = dependencies or []
        self.validation = validation or []
        self.sla_ms = sla_ms
        self.error_handling = error_handling or {}

class SubProcess:
    """
    Represents a reusable process component with input/output specifications.
    """
    def __init__(self, name: str, input_spec: Optional[Dict[str, Any]] = None, output_spec: Optional[Dict[str, Any]] = None):
        self.name = name
        self.input_spec = input_spec or {}
        self.output_spec = output_spec or {}

class SubProcessCall:
    """
    Represents an integration point between a main process and a sub-process.
    """
    def __init__(self, sub_process: SubProcess, call_args: Optional[Dict[str, Any]] = None):
        self.sub_process = sub_process
        self.call_args = call_args or {}
