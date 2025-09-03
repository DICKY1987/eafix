"""
HUEY_P Trading Interface - Tabs Package
Contains UI tab implementations for different application views
"""

from .live_dashboard import LiveDashboard
from .trade_history import TradeHistory
from .system_status import SystemStatus as SystemStatusTab
from .settings_panel import SettingsPanel
from .matrix_parameters import MatrixParametersTab

__all__ = [
    'LiveDashboard',
    'TradeHistory',
    'SystemStatusTab',
    'SettingsPanel',
    'MatrixParametersTab'
]
