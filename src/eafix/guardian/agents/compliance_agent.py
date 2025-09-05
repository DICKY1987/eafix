"""Compliance agent for trading rule enforcement."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum


class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    VIOLATION = "violation"
    WARNING = "warning"


@dataclass
class ComplianceRule:
    """Represents a trading compliance rule."""
    name: str
    description: str
    rule_type: str  # e.g., "position_size", "daily_loss", "exposure"
    threshold: float
    enabled: bool = True


@dataclass
class ComplianceViolation:
    """Represents a compliance violation."""
    rule_name: str
    violation_type: str
    current_value: float
    threshold: float
    severity: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False


@dataclass
class ComplianceAgent:
    """Production compliance agent for trading rule enforcement."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rules: Dict[str, ComplianceRule] = {}
        self.violations: List[ComplianceViolation] = []
        self.monitoring_enabled = True
        
        # Initialize default rules
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """Setup default compliance rules."""
        default_rules = [
            ComplianceRule("max_position_size", "Maximum position size per symbol", "position_size", 100000.0),
            ComplianceRule("daily_loss_limit", "Maximum daily loss limit", "daily_loss", 5000.0),
            ComplianceRule("max_exposure", "Maximum total exposure", "exposure", 500000.0),
            ComplianceRule("max_symbols", "Maximum number of symbols", "symbol_count", 10),
            ComplianceRule("order_frequency", "Maximum orders per minute", "order_frequency", 20)
        ]
        
        for rule in default_rules:
            self.rules[rule.name] = rule
    
    def log(self, message: str) -> None:
        """Log compliance message."""
        self.logger.info(f"ComplianceAgent: {message}")
    
    def check_position_size(self, symbol: str, size: float) -> ComplianceStatus:
        """Check if position size complies with rules."""
        rule = self.rules.get("max_position_size")
        if not rule or not rule.enabled:
            return ComplianceStatus.COMPLIANT
        
        if size > rule.threshold:
            violation = ComplianceViolation(
                rule_name=rule.name,
                violation_type="position_size_exceeded",
                current_value=size,
                threshold=rule.threshold,
                severity="HIGH"
            )
            self.violations.append(violation)
            self.log(f"Position size violation for {symbol}: {size} > {rule.threshold}")
            return ComplianceStatus.VIOLATION
        
        return ComplianceStatus.COMPLIANT
    
    def check_daily_loss(self, current_loss: float) -> ComplianceStatus:
        """Check daily loss compliance."""
        rule = self.rules.get("daily_loss_limit")
        if not rule or not rule.enabled:
            return ComplianceStatus.COMPLIANT
        
        if abs(current_loss) > rule.threshold:
            violation = ComplianceViolation(
                rule_name=rule.name,
                violation_type="daily_loss_exceeded",
                current_value=abs(current_loss),
                threshold=rule.threshold,
                severity="CRITICAL"
            )
            self.violations.append(violation)
            self.log(f"Daily loss limit violation: {current_loss} > {rule.threshold}")
            return ComplianceStatus.VIOLATION
        
        return ComplianceStatus.COMPLIANT
    
    def check_exposure(self, total_exposure: float) -> ComplianceStatus:
        """Check total exposure compliance."""
        rule = self.rules.get("max_exposure")
        if not rule or not rule.enabled:
            return ComplianceStatus.COMPLIANT
        
        if total_exposure > rule.threshold:
            violation = ComplianceViolation(
                rule_name=rule.name,
                violation_type="exposure_exceeded",
                current_value=total_exposure,
                threshold=rule.threshold,
                severity="HIGH"
            )
            self.violations.append(violation)
            self.log(f"Exposure limit violation: {total_exposure} > {rule.threshold}")
            return ComplianceStatus.VIOLATION
        
        return ComplianceStatus.COMPLIANT
    
    def get_active_violations(self) -> List[ComplianceViolation]:
        """Get all unresolved violations."""
        return [v for v in self.violations if not v.resolved]
    
    def resolve_violation(self, violation_index: int) -> bool:
        """Mark a violation as resolved."""
        if 0 <= violation_index < len(self.violations):
            self.violations[violation_index].resolved = True
            self.log(f"Resolved violation: {self.violations[violation_index].rule_name}")
            return True
        return False
    
    def add_rule(self, rule: ComplianceRule) -> None:
        """Add a new compliance rule."""
        self.rules[rule.name] = rule
        self.log(f"Added compliance rule: {rule.name}")
    
    def disable_rule(self, rule_name: str) -> bool:
        """Disable a compliance rule."""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = False
            self.log(f"Disabled compliance rule: {rule_name}")
            return True
        return False
