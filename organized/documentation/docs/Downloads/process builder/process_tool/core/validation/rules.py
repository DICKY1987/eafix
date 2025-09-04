"""
Reusable validation rules for process steps.
"""
from ..models.process_step import ProcessStep

def is_valid_step(step: ProcessStep) -> bool:
    """
    Check if a ProcessStep has required fields.
    """
    return bool(step.step_id and step.actor and step.description)
