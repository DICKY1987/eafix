"""Core package for the HUEY_P trading interface."""

from importlib import import_module
from typing import Any

__all__ = [
    'AppController',
    'DatabaseManager',
    'EAConnector',
    'SystemStatus',
    'LiveMetrics',
    'TradeData',
]

_definitions = {
    'AppController': 'core.app_controller',
    'DatabaseManager': 'core.database_manager',
    'EAConnector': 'core.ea_connector',
    'SystemStatus': 'core.data_models',
    'LiveMetrics': 'core.data_models',
    'TradeData': 'core.data_models',
}


def __getattr__(name: str) -> Any:  # pragma: no cover - thin wrapper
    if name in _definitions:
        module = import_module(_definitions[name])
        return getattr(module, name)
    raise AttributeError(f"module 'core' has no attribute '{name}'")
