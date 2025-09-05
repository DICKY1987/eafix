"""
Centralized State Management for HUEY_P GUI
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import threading
import os
from .event_bus import event_bus

@dataclass
class RiskMetrics:
    daily_drawdown: float = 0.0
    daily_limit: float = 2.0
    portfolio_risk: float = 0.0
    max_correlation: float = 0.0
    session_cap_used: float = 0.0
    session_cap_limit: float = 1.5
    last_update: datetime = field(default_factory=datetime.now)

@dataclass
class ConnectivityStatus:
    dde_connected: bool = False
    last_update: Optional[datetime] = None
    symbol_count: int = 0
    connection_quality: str = "unknown"  # "excellent", "good", "poor", "disconnected"

@dataclass
class MarketData:
    symbols: Dict[str, Dict[str, float]] = field(default_factory=dict)  # symbol -> {timeframe: pct_change}
    currency_strength: Dict[str, Dict[str, float]] = field(default_factory=dict)  # currency -> {timeframe: strength}
    last_update: datetime = field(default_factory=datetime.now)

@dataclass
class UIPreferences:
    theme: str = "dark"
    sound_enabled: bool = False
    update_frequency: int = 1000  # milliseconds
    risk_alert_threshold: float = 0.9
    column_widths: Dict[str, int] = field(default_factory=dict)
    workspace_layout: str = "default"

@dataclass
class SystemHealth:
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    frame_rate: float = 0.0
    event_queue_size: int = 0
    last_check: datetime = field(default_factory=datetime.now)

@dataclass
class TradingState:
    """Current trading state information"""
    is_trading_allowed: bool = True
    last_signal_time: Optional[datetime] = None
    active_positions: int = 0
    pending_orders: int = 0
    last_trade_result: str = ""

class StateManager:
    """Centralized state management with automatic persistence"""
    
    def __init__(self, config_path: str = "config/app_state.json"):
        self.config_path = config_path
        self._lock = threading.RLock()
        
        # Ensure config directory exists
        config_dir = os.path.dirname(config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        # Initialize state components
        self.risk_metrics = RiskMetrics()
        self.connectivity = ConnectivityStatus()
        self.market_data = MarketData()
        self.ui_preferences = UIPreferences()
        self.system_health = SystemHealth()
        self.trading_state = TradingState()
        
        # Load persisted state
        self.load_state()
        
        # Subscribe to events for state updates
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup event handlers for state updates"""
        event_bus.subscribe("risk_update", self._handle_risk_update)
        event_bus.subscribe("connectivity_update", self._handle_connectivity_update)
        event_bus.subscribe("market_data_update", self._handle_market_data_update)
        event_bus.subscribe("ui_preferences_update", self._handle_ui_preferences_update)
        event_bus.subscribe("system_health_update", self._handle_system_health_update)
        event_bus.subscribe("trading_state_update", self._handle_trading_state_update)
    
    def _handle_risk_update(self, event):
        """Handle risk metric updates"""
        with self._lock:
            data = event.data
            self.risk_metrics = RiskMetrics(
                daily_drawdown=data.get('daily_drawdown', self.risk_metrics.daily_drawdown),
                daily_limit=data.get('daily_limit', self.risk_metrics.daily_limit),
                portfolio_risk=data.get('portfolio_risk', self.risk_metrics.portfolio_risk),
                max_correlation=data.get('max_correlation', self.risk_metrics.max_correlation),
                session_cap_used=data.get('session_cap_used', self.risk_metrics.session_cap_used),
                session_cap_limit=data.get('session_cap_limit', self.risk_metrics.session_cap_limit),
                last_update=datetime.now()
            )
    
    def _handle_connectivity_update(self, event):
        """Handle connectivity status updates"""
        with self._lock:
            data = event.data
            self.connectivity = ConnectivityStatus(
                dde_connected=data.get('dde_connected', self.connectivity.dde_connected),
                last_update=datetime.now(),
                symbol_count=data.get('symbol_count', self.connectivity.symbol_count),
                connection_quality=data.get('connection_quality', self.connectivity.connection_quality)
            )
    
    def _handle_market_data_update(self, event):
        """Handle market data updates"""
        with self._lock:
            data = event.data
            if 'symbols' in data:
                self.market_data.symbols.update(data['symbols'])
            if 'currency_strength' in data:
                self.market_data.currency_strength.update(data['currency_strength'])
            self.market_data.last_update = datetime.now()
    
    def _handle_ui_preferences_update(self, event):
        """Handle UI preferences updates"""
        with self._lock:
            data = event.data
            for key, value in data.items():
                if hasattr(self.ui_preferences, key):
                    setattr(self.ui_preferences, key, value)
            self.save_state()  # Persist UI preferences immediately
    
    def _handle_system_health_update(self, event):
        """Handle system health updates"""
        with self._lock:
            data = event.data
            self.system_health = SystemHealth(
                cpu_usage=data.get('cpu_usage', self.system_health.cpu_usage),
                memory_usage=data.get('memory_usage', self.system_health.memory_usage),
                frame_rate=data.get('frame_rate', self.system_health.frame_rate),
                event_queue_size=data.get('event_queue_size', self.system_health.event_queue_size),
                last_check=datetime.now()
            )
    
    def _handle_trading_state_update(self, event):
        """Handle trading state updates"""
        with self._lock:
            data = event.data
            for key, value in data.items():
                if hasattr(self.trading_state, key):
                    setattr(self.trading_state, key, value)
    
    def get_risk_metrics(self) -> RiskMetrics:
        """Get current risk metrics"""
        with self._lock:
            return self.risk_metrics
    
    def get_connectivity_status(self) -> ConnectivityStatus:
        """Get current connectivity status"""
        with self._lock:
            return self.connectivity
    
    def get_market_data(self) -> MarketData:
        """Get current market data"""
        with self._lock:
            return self.market_data
    
    def get_ui_preferences(self) -> UIPreferences:
        """Get current UI preferences"""
        with self._lock:
            return self.ui_preferences
    
    def get_system_health(self) -> SystemHealth:
        """Get current system health"""
        with self._lock:
            return self.system_health
    
    def get_trading_state(self) -> TradingState:
        """Get current trading state"""
        with self._lock:
            return self.trading_state
    
    def is_action_allowed(self) -> tuple[bool, str]:
        """Check if trading actions are allowed based on current state"""
        with self._lock:
            # Check connectivity
            if not self.connectivity.dde_connected:
                return False, "DDE connection lost"
            
            # Check daily drawdown limit
            dd_ratio = abs(self.risk_metrics.daily_drawdown) / self.risk_metrics.daily_limit
            if dd_ratio >= 1.0:
                return False, f"Daily drawdown limit reached ({self.risk_metrics.daily_limit}%)"
            
            # Check correlation limit
            if self.risk_metrics.max_correlation > 0.7:
                return False, f"Correlation too high ({self.risk_metrics.max_correlation:.2f} > 0.70)"
            
            # Check session cap
            if self.risk_metrics.session_cap_used >= self.risk_metrics.session_cap_limit:
                return False, f"Session cap reached ({self.risk_metrics.session_cap_limit}%)"
            
            # Check trading state
            if not self.trading_state.is_trading_allowed:
                return False, "Trading manually disabled"
            
            return True, "Actions allowed"
    
    def save_state(self):
        """Save current state to disk"""
        try:
            state_dict = {
                'ui_preferences': {
                    'theme': self.ui_preferences.theme,
                    'sound_enabled': self.ui_preferences.sound_enabled,
                    'update_frequency': self.ui_preferences.update_frequency,
                    'risk_alert_threshold': self.ui_preferences.risk_alert_threshold,
                    'column_widths': self.ui_preferences.column_widths,
                    'workspace_layout': self.ui_preferences.workspace_layout
                }
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(state_dict, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save state: {e}")
    
    def load_state(self):
        """Load persisted state from disk"""
        try:
            if not os.path.exists(self.config_path):
                return  # No saved state yet
                
            with open(self.config_path, 'r') as f:
                state_dict = json.load(f)
                
            if 'ui_preferences' in state_dict:
                ui_prefs = state_dict['ui_preferences']
                self.ui_preferences = UIPreferences(
                    theme=ui_prefs.get('theme', 'dark'),
                    sound_enabled=ui_prefs.get('sound_enabled', False),
                    update_frequency=ui_prefs.get('update_frequency', 1000),
                    risk_alert_threshold=ui_prefs.get('risk_alert_threshold', 0.9),
                    column_widths=ui_prefs.get('column_widths', {}),
                    workspace_layout=ui_prefs.get('workspace_layout', 'default')
                )
                
        except Exception as e:
            print(f"Failed to load state: {e}")

# Global state manager instance  
state_manager = StateManager()