"""
HUEY_P Trading Interface - Data Models
Defines data structures for system status, metrics, and trade data
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

class EAState(Enum):
    """EA operational states"""
    IDLE = "IDLE"
    ORDERS_PLACED = "ORDERS_PLACED"
    TRADE_TRIGGERED = "TRADE_TRIGGERED"
    PAUSED = "PAUSED"
    UNKNOWN = "UNKNOWN"

class RecoveryState(Enum):
    """EA recovery states"""
    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"
    EMERGENCY = "EMERGENCY"
    UNKNOWN = "UNKNOWN"

class OrderType(Enum):
    """Trade order types"""
    BUY = "BUY"
    SELL = "SELL"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"

class TradeStatus(Enum):
    """Trade status types"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"

@dataclass
class TradeData:
    """Individual trade data structure"""
    ticket: int
    symbol: str
    order_type: OrderType
    volume: float
    open_price: float
    close_price: Optional[float] = None
    open_time: Optional[datetime] = None
    close_time: Optional[datetime] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    profit: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    comment: str = ""
    status: TradeStatus = TradeStatus.OPEN
    
    @property
    def net_profit(self) -> float:
        """Calculate net profit including commission and swap"""
        return self.profit + self.commission + self.swap
    
    @property
    def duration_minutes(self) -> Optional[int]:
        """Calculate trade duration in minutes"""
        if self.open_time and self.close_time:
            delta = self.close_time - self.open_time
            return int(delta.total_seconds() / 60)
        return None
    
    @property
    def is_profitable(self) -> bool:
        """Check if trade is profitable"""
        return self.net_profit > 0

@dataclass
class LiveMetrics:
    """Real-time trading metrics"""
    ea_state: EAState = EAState.UNKNOWN
    recovery_state: RecoveryState = RecoveryState.UNKNOWN
    active_trades: int = 0
    daily_profit: float = 0.0
    account_equity: float = 0.0
    account_balance: float = 0.0
    daily_drawdown: float = 0.0
    max_drawdown: float = 0.0
    uptime_seconds: int = 0
    trade_count: int = 0
    win_count: int = 0
    loss_count: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    last_trade_time: Optional[datetime] = None
    last_update: Optional[datetime] = None
    
    # Risk metrics
    risk_percent: float = 0.0
    margin_used: float = 0.0
    margin_available: float = 0.0
    
    # Performance metrics
    total_profit: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    
    def update_from_dict(self, data: Dict[str, Any]):
        """Update metrics from dictionary data"""
        for key, value in data.items():
            if hasattr(self, key):
                if key in ['ea_state'] and isinstance(value, str):
                    try:
                        setattr(self, key, EAState(value))
                    except ValueError:
                        setattr(self, key, EAState.UNKNOWN)
                elif key in ['recovery_state'] and isinstance(value, str):
                    try:
                        setattr(self, key, RecoveryState(value))
                    except ValueError:
                        setattr(self, key, RecoveryState.UNKNOWN)
                elif key in ['last_trade_time', 'last_update'] and isinstance(value, str):
                    try:
                        setattr(self, key, datetime.fromisoformat(value))
                    except (ValueError, TypeError):
                        pass
                else:
                    setattr(self, key, value)
        
        self.last_update = datetime.now()
    
    @property
    def uptime_formatted(self) -> str:
        """Get formatted uptime string"""
        if self.uptime_seconds < 60:
            return f"{self.uptime_seconds}s"
        elif self.uptime_seconds < 3600:
            return f"{self.uptime_seconds // 60}m"
        else:
            hours = self.uptime_seconds // 3600
            minutes = (self.uptime_seconds % 3600) // 60
            return f"{hours}h {minutes}m"

@dataclass
class SystemStatus:
    """System health and status information"""
    database_connected: bool = False
    ea_bridge_connected: bool = False
    last_heartbeat: Optional[datetime] = None
    error_count: int = 0
    warning_count: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_latency: float = 0.0
    
    # Component status
    components: Dict[str, str] = field(default_factory=dict)
    
    # Recent errors
    recent_errors: List[str] = field(default_factory=list)
    
    # System configuration
    config_valid: bool = True
    config_errors: List[str] = field(default_factory=list)
    
    def update_from_heartbeat(self, heartbeat_data: Dict[str, Any]):
        """Update status from heartbeat data"""
        self.last_heartbeat = datetime.now()
        
        # Update from heartbeat payload
        if 'error_count' in heartbeat_data:
            self.error_count = heartbeat_data['error_count']
        if 'warning_count' in heartbeat_data:
            self.warning_count = heartbeat_data['warning_count']
        if 'cpu_usage' in heartbeat_data:
            self.cpu_usage = heartbeat_data['cpu_usage']
        if 'memory_usage' in heartbeat_data:
            self.memory_usage = heartbeat_data['memory_usage']
    
    @property
    def overall_health(self) -> str:
        """Get overall system health status"""
        if not self.database_connected or not self.ea_bridge_connected:
            return "CRITICAL"
        elif self.error_count > 5 or self.cpu_usage > 90:
            return "WARNING"
        elif self.error_count > 0:
            return "CAUTION"
        else:
            return "HEALTHY"
    
    @property
    def connection_status(self) -> str:
        """Get connection status summary"""
        db_status = "✓" if self.database_connected else "✗"
        ea_status = "✓" if self.ea_bridge_connected else "✗"
        return f"DB: {db_status} | EA: {ea_status}"

@dataclass
class PerformanceMetrics:
    """Performance analysis metrics"""
    total_trades: int = 0
    total_wins: int = 0
    total_losses: int = 0
    total_profit: float = 0.0
    total_commission: float = 0.0
    total_swap: float = 0.0
    
    # Win/Loss metrics
    avg_win: float = 0.0
    avg_loss: float = 0.0
    max_win: float = 0.0
    max_loss: float = 0.0
    
    # Time-based metrics
    avg_trade_duration: float = 0.0  # in minutes
    max_trade_duration: float = 0.0
    min_trade_duration: float = 0.0
    
    # Risk metrics
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0  # in days
    recovery_factor: float = 0.0
    
    # Efficiency metrics
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.total_trades == 0:
            return 0.0
        return (self.total_wins / self.total_trades) * 100
    
    @property
    def net_profit(self) -> float:
        """Calculate net profit including all costs"""
        return self.total_profit + self.total_commission + self.total_swap
    
    @property
    def average_trade(self) -> float:
        """Calculate average profit per trade"""
        if self.total_trades == 0:
            return 0.0
        return self.net_profit / self.total_trades

@dataclass
class SignalData:
    """Trading signal data structure"""
    signal_id: str
    symbol: str
    signal_type: str
    confidence: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: Optional[datetime] = None
    executed: bool = False
    result: Optional[str] = None
    source: str = "manual"
    category: str = "standard"
    comment: str = ""
    
    @property
    def age_minutes(self) -> Optional[int]:
        """Get signal age in minutes"""
        if self.timestamp:
            delta = datetime.now() - self.timestamp
            return int(delta.total_seconds() / 60)
        return None

@dataclass
class AccountInfo:
    """Account information structure"""
    account_number: int = 0
    account_name: str = ""
    server: str = ""
    currency: str = "USD"
    leverage: int = 1
    balance: float = 0.0
    equity: float = 0.0
    margin: float = 0.0
    free_margin: float = 0.0
    margin_level: float = 0.0
    profit: float = 0.0
    
    @property
    def margin_call_level(self) -> float:
        """Calculate margin call level percentage"""
        if self.margin > 0:
            return (self.equity / self.margin) * 100
        return 0.0

@dataclass
class MarketInfo:
    """Market information for a symbol"""
    symbol: str
    bid: float = 0.0
    ask: float = 0.0
    last: float = 0.0
    volume: int = 0
    time: Optional[datetime] = None
    
    @property
    def spread(self) -> float:
        """Calculate spread in points"""
        return self.ask - self.bid
    
    @property
    def spread_pips(self) -> float:
        """Calculate spread in pips (assuming 4-5 digit broker)"""
        if "JPY" in self.symbol:
            return self.spread * 100  # 2-digit JPY pairs
        else:
            return self.spread * 10000  # 4-digit major pairs

@dataclass
class AlertConfig:
    """Alert configuration structure"""
    enabled: bool = True
    email_alerts: bool = False
    sound_alerts: bool = True
    popup_alerts: bool = True
    
    # Alert thresholds
    profit_threshold: float = 100.0
    loss_threshold: float = -50.0
    drawdown_threshold: float = 5.0
    equity_threshold: float = 1000.0
    
    # Email settings
    email_address: str = ""
    smtp_server: str = ""
    smtp_port: int = 587