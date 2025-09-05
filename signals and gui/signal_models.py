"""
Signal data models for the trading system.
Defines the structure of trading signals and related data.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, conint, confloat
import json


class SignalDirection(str, Enum):
    """Trading signal direction"""
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"
    CLOSE = "CLOSE"


class SignalStatus(str, Enum):
    """Signal status"""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    EXECUTED = "EXECUTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"


class StrategyType(str, Enum):
    """Trading strategy types"""
    BREAKOUT = "BREAKOUT_STRATEGY"
    REVERSAL = "REVERSAL_STRATEGY"
    TREND_FOLLOWING = "TREND_FOLLOWING"
    MEAN_REVERSION = "MEAN_REVERSION"
    MOMENTUM = "MOMENTUM"
    ARBITRAGE = "ARBITRAGE"
    CUSTOM = "CUSTOM"


class SignalPriority(str, Enum):
    """Signal priority levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MarketCondition(str, Enum):
    """Market condition types"""
    TRENDING = "TRENDING"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"
    QUIET = "QUIET"
    BREAKOUT = "BREAKOUT"


class SignalMetadata(BaseModel):
    """Additional signal metadata"""
    strategy_version: str = Field(default="1.0.0")
    market_condition: Optional[MarketCondition] = Field(default=None)
    correlation_pairs: List[str] = Field(default_factory=list)
    news_impact: Optional[str] = Field(default=None)
    volatility_index: Optional[confloat(ge=0, le=100)] = Field(default=None)
    custom_data: Dict[str, Any] = Field(default_factory=dict)
    
    def to_json_string(self) -> str:
        """Convert metadata to JSON string"""
        return json.dumps(self.dict(exclude_none=True))
    
    @classmethod
    def from_json_string(cls, json_str: str) -> 'SignalMetadata':
        """Create metadata from JSON string"""
        return cls(**json.loads(json_str))


class TradingSignal(BaseModel):
    """Main trading signal model"""
    # Required fields
    id: str = Field(..., regex=r'^[A-Za-z0-9\-_]+$')
    symbol: str = Field(..., regex=r'^[A-Z]{6}$|^XAU[A-Z]{3}$|^XAG[A-Z]{3}$')
    direction: SignalDirection = Field(...)
    confidence: confloat(ge=0.0, le=1.0) = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Strategy information
    strategy_id: str = Field(..., regex=r'^[A-Z_]+$')
    strategy_type: StrategyType = Field(default=StrategyType.CUSTOM)
    parameter_set: conint(ge=1, le=10) = Field(default=1)
    
    # Signal details
    entry_price: Optional[float] = Field(default=None, gt=0)
    stop_loss: Optional[float] = Field(default=None, gt=0)
    take_profit: Optional[float] = Field(default=None, gt=0)
    expiry_time: Optional[datetime] = Field(default=None)
    
    # Risk parameters
    risk_score: confloat(ge=0.0, le=1.0) = Field(default=0.5)
    suggested_lot_size: Optional[confloat(ge=0.01, le=100.0)] = Field(default=None)
    max_slippage: Optional[conint(ge=0, le=50)] = Field(default=3)
    
    # Status and metadata
    status: SignalStatus = Field(default=SignalStatus.PENDING)
    priority: SignalPriority = Field(default=SignalPriority.MEDIUM)
    metadata: SignalMetadata = Field(default_factory=SignalMetadata)
    
    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    executed_at: Optional[datetime] = Field(default=None)
    
    @validator('stop_loss')
    def validate_stop_loss(cls, v, values):
        """Validate stop loss relative to direction"""
        if v is not None and 'entry_price' in values and values['entry_price'] is not None:
            if values.get('direction') == SignalDirection.BUY and v >= values['entry_price']:
                raise ValueError("Stop loss must be below entry price for BUY signals")
            elif values.get('direction') == SignalDirection.SELL and v <= values['entry_price']:
                raise ValueError("Stop loss must be above entry price for SELL signals")
        return v
    
    @validator('take_profit')
    def validate_take_profit(cls, v, values):
        """Validate take profit relative to direction"""
        if v is not None and 'entry_price' in values and values['entry_price'] is not None:
            if values.get('direction') == SignalDirection.BUY and v <= values['entry_price']:
                raise ValueError("Take profit must be above entry price for BUY signals")
            elif values.get('direction') == SignalDirection.SELL and v >= values['entry_price']:
                raise ValueError("Take profit must be below entry price for SELL signals")
        return v
    
    def to_csv_row(self) -> Dict[str, Any]:
        """Convert signal to CSV row format"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'direction': self.direction.value,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'strategy_id': self.strategy_id,
            'parameter_set': self.parameter_set,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'status': self.status.value,
            'metadata': self.metadata.to_json_string()
        }
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, Any]) -> 'TradingSignal':
        """Create signal from CSV row"""
        # Parse metadata if present
        metadata = SignalMetadata()
        if 'metadata' in row and row['metadata']:
            try:
                metadata = SignalMetadata.from_json_string(row['metadata'])
            except:
                pass
        
        return cls(
            id=row['id'],
            symbol=row['symbol'],
            direction=SignalDirection(row['direction']),
            confidence=float(row['confidence']),
            timestamp=datetime.fromisoformat(row['timestamp']),
            strategy_id=row['strategy_id'],
            parameter_set=int(row.get('parameter_set', 1)),
            entry_price=float(row['entry_price']) if row.get('entry_price') else None,
            stop_loss=float(row['stop_loss']) if row.get('stop_loss') else None,
            take_profit=float(row['take_profit']) if row.get('take_profit') else None,
            status=SignalStatus(row.get('status', 'PENDING')),
            metadata=metadata
        )
    
    def update_status(self, new_status: SignalStatus):
        """Update signal status with timestamp"""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        if new_status == SignalStatus.EXECUTED:
            self.executed_at = datetime.utcnow()
    
    def is_valid(self) -> bool:
        """Check if signal is still valid"""
        if self.status not in [SignalStatus.PENDING, SignalStatus.ACTIVE]:
            return False
        if self.expiry_time and datetime.utcnow() > self.expiry_time:
            return False
        return True
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Enum: lambda v: v.value
        }


class SignalBatch(BaseModel):
    """Batch of trading signals"""
    batch_id: str = Field(..., regex=r'^[A-Za-z0-9\-_]+$')
    signals: List[TradingSignal] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total_signals: conint(ge=0) = Field(default=0)
    
    def add_signal(self, signal: TradingSignal):
        """Add a signal to the batch"""
        self.signals.append(signal)
        self.total_signals = len(self.signals)
    
    def get_by_symbol(self, symbol: str) -> List[TradingSignal]:
        """Get all signals for a specific symbol"""
        return [s for s in self.signals if s.symbol == symbol]
    
    def get_active_signals(self) -> List[TradingSignal]:
        """Get all active signals"""
        return [s for s in self.signals if s.is_valid()]


class SignalResponse(BaseModel):
    """Response model for signal requests"""
    success: bool = Field(default=True)
    signal: Optional[TradingSignal] = Field(default=None)
    error: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[float] = Field(default=None)
    
    @classmethod
    def success_response(cls, signal: TradingSignal, processing_time_ms: float = None) -> 'SignalResponse':
        """Create a success response"""
        return cls(
            success=True,
            signal=signal,
            processing_time_ms=processing_time_ms
        )
    
    @classmethod
    def error_response(cls, error_message: str) -> 'SignalResponse':
        """Create an error response"""
        return cls(
            success=False,
            error=error_message
        )


class SignalStatistics(BaseModel):
    """Signal statistics model"""
    symbol: str
    total_signals: conint(ge=0) = Field(default=0)
    buy_signals: conint(ge=0) = Field(default=0)
    sell_signals: conint(ge=0) = Field(default=0)
    executed_signals: conint(ge=0) = Field(default=0)
    cancelled_signals: conint(ge=0) = Field(default=0)
    average_confidence: confloat(ge=0.0, le=1.0) = Field(default=0.0)
    win_rate: Optional[confloat(ge=0.0, le=1.0)] = Field(default=None)
    profit_factor: Optional[float] = Field(default=None)
    
    def update_from_signals(self, signals: List[TradingSignal]):
        """Update statistics from a list of signals"""
        if not signals:
            return
        
        self.total_signals = len(signals)
        self.buy_signals = len([s for s in signals if s.direction == SignalDirection.BUY])
        self.sell_signals = len([s for s in signals if s.direction == SignalDirection.SELL])
        self.executed_signals = len([s for s in signals if s.status == SignalStatus.EXECUTED])
        self.cancelled_signals = len([s for s in signals if s.status == SignalStatus.CANCELLED])
        
        if self.total_signals > 0:
            self.average_confidence = sum(s.confidence for s in signals) / self.total_signals