"""
Schema validation logic for process flows.
"""
from ..models.process_flow import ProcessFlow
from ..models.process_step import ProcessStep

def validate_schema(process_flow: ProcessFlow) -> bool:
    """
    Validate the schema of a ProcessFlow object.
    Returns True if valid, raises ValidationError otherwise.
    """
    # Example: Ensure each section has a name and steps are ProcessStep
    for section in process_flow.sections:
        if not section.name:
            raise ValueError("Section must have a name.")
        for step in section.steps:
            if not isinstance(step, ProcessStep):
                raise TypeError("All steps must be ProcessStep instances.")
    return True
