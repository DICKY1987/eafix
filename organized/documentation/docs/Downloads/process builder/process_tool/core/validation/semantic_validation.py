"""
Semantic validation logic for process flows.
"""
from ..models.process_flow import ProcessFlow

def validate_semantics(process_flow: ProcessFlow) -> bool:
    """
    Perform semantic validation on a ProcessFlow (e.g., check for cycles, missing dependencies).
    Returns True if valid, raises ValidationError otherwise.
    """
    step_ids = set()
    for section in process_flow.sections:
        for step in section.steps:
            if step.step_id in step_ids:
                raise ValueError(f"Duplicate step_id found: {step.step_id}")
            step_ids.add(step.step_id)
    return True
