"""
Core data models for the Atomic Process Framework.
Defines ProcessFlow, ProcessSection, ProcessStep, SubProcess, SubProcessCall.
"""

class ProcessFlow:
    """Container for complete process documentation."""
    pass

class ProcessSection:
    """Major process sections (e.g., Initialization, Processing)."""
    pass

class ProcessStep:
    """Individual atomic actions with SLA, validation, and error handling."""
    pass

class SubProcess:
    """Reusable process components with input/output specifications."""
    pass

class SubProcessCall:
    """Integration points between main and sub-processes."""
    pass
