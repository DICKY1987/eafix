"""Unified error classes for APF."""
class SchemaError(Exception):
    pass
class ValidationError(Exception):
    pass
class PluginError(Exception):
    pass
class OrchestrationError(Exception):
    pass
