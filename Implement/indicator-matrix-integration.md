# New Indicator Integration with Matrix System - Design Brainstorm

## Overview

This document outlines a systematic approach to integrate new indicators into the existing HUEY_P matrix system while maintaining safety through conservative defaults and providing a clear pathway to production deployment.

---

## 1. Indicator Lifecycle Management

### 1.1 Indicator Status States

```python
class IndicatorStatus(Enum):
    EXPERIMENTAL = "experimental"    # New indicator, ultra-conservative
    TESTING = "testing"             # Proven safe, moderate settings
    VALIDATED = "validated"         # Performance verified, standard settings
    PRODUCTION = "production"       # Full deployment, optimized settings
    DEPRECATED = "deprecated"       # Being phased out
    DISABLED = "disabled"          # Temporarily disabled
```

### 1.2 Promotion Pipeline

```
EXPERIMENTAL → TESTING → VALIDATED → PRODUCTION
     ↓            ↓           ↓           ↓
   30 days     60 trades   Sharpe >1.0   Manual review
   No losses   Win rate    Max DD <2%    Risk committee
   <1% risk    >40%        Stable       approval
```

---

## 2. Conservative Default Framework

### 2.1 Risk-Graduated Parameter Templates

```python
# Conservative parameter templates by status
INDICATOR_DEFAULTS = {
    "EXPERIMENTAL": {
        "global_risk_percent": 0.5,      # Ultra-low risk
        "confidence_threshold": 0.85,     # High confidence required
        "stop_loss_pips": 15,             # Tight stops
        "take_profit_pips": 30,           # Conservative targets
        "max_positions": 1,               # Single position only
        "cooldown_minutes": 60,           # Long cooldowns
        "enabled_sessions": ["LONDON"],   # Limited sessions
        "risk_multiplier": 0.25,          # Quarter normal risk
        "signal_strength_required": 0.9   # Very strong signals only
    },
    
    "TESTING": {
        "global_risk_percent": 1.0,       # Low risk
        "confidence_threshold": 0.75,     # Moderate confidence
        "stop_loss_pips": 12,             # Standard stops
        "take_profit_pips": 24,           # Standard targets
        "max_positions": 2,               # Two positions max
        "cooldown_minutes": 30,           # Moderate cooldowns
        "enabled_sessions": ["LONDON", "NEW_YORK"],
        "risk_multiplier": 0.5,           # Half normal risk
        "signal_strength_required": 0.75
    },
    
    "VALIDATED": {
        "global_risk_percent": 1.5,       # Normal risk
        "confidence_threshold": 0.65,     # Standard confidence
        "stop_loss_pips": 10,             # Normal stops
        "take_profit_pips": 20,           # Normal targets
        "max_positions": 3,               # Multiple positions
        "cooldown_minutes": 15,           # Standard cooldowns
        "enabled_sessions": ["LONDON", "NEW_YORK", "TOKYO"],
        "risk_multiplier": 0.75,          # Three-quarter risk
        "signal_strength_required": 0.65
    },
    
    "PRODUCTION": {
        "global_risk_percent": 2.5,       # Full risk (under 3.5% cap)
        "confidence_threshold": 0.55,     # Lower threshold
        "stop_loss_pips": 8,              # Optimized stops
        "take_profit_pips": 16,           # Optimized targets
        "max_positions": 5,               # Full deployment
        "cooldown_minutes": 5,            # Minimal cooldowns
        "enabled_sessions": ["ALL"],       # All sessions
        "risk_multiplier": 1.0,           # Full risk
        "signal_strength_required": 0.55
    }
}
```

---

## 3. Matrix Integration Architecture

### 3.1 Extended Signal Type System

```python
# Extended signal types to accommodate new indicators
CORE_SIGNALS = [
    "ECO_HIGH", "ECO_MED", 
    "ANTICIPATION_1HR", "ANTICIPATION_8HR",
    "EQUITY_OPEN_ASIA", "EQUITY_OPEN_EUROPE", "EQUITY_OPEN_USA"
]

# Dynamic indicator signals with status prefix
INDICATOR_SIGNALS = [
    "EXP_PERCENT_CHANGE",     # Experimental percent change
    "EXP_CURRENCY_STRENGTH",  # Experimental currency strength
    "TEST_RSI_DIVERGENCE",    # Testing RSI divergence
    "VAL_MACD_CROSSOVER",     # Validated MACD crossover
    "PROD_SMA_BREAKOUT"       # Production SMA breakout
]

ALL_SIGNALS = CORE_SIGNALS + INDICATOR_SIGNALS
```

### 3.2 Dynamic Matrix Expansion

```python
class DynamicMatrixManager:
    def __init__(self):
        self.static_combinations = 1008  # Original matrix size
        self.dynamic_combinations = {}   # New indicator combinations
        
    def register_new_indicator(self, indicator_name: str, status: IndicatorStatus):
        """Register new indicator and generate matrix combinations"""
        signal_type = f"{status.value.upper()[:3]}_{indicator_name.upper()}"
        
        # Generate combinations for new signal type
        combinations = self._generate_indicator_combinations(signal_type, status)
        self.dynamic_combinations[signal_type] = combinations
        
        # Create conservative parameter sets
        self._create_conservative_parameter_sets(signal_type, status)
        
    def _generate_indicator_combinations(self, signal_type: str, status: IndicatorStatus):
        """Generate matrix combinations for new indicator"""
        combinations = []
        
        # Reduced combinations for experimental indicators
        if status == IndicatorStatus.EXPERIMENTAL:
            outcomes = ["WIN", "LOSS"]  # Only basic outcomes
            proximities = ["LONG", "EXTENDED"]  # Safe proximities only
        else:
            outcomes = ["WIN", "LOSS", "BE", "SKIP", "REJECT", "CANCEL"]
            proximities = ["IMMEDIATE", "SHORT", "LONG", "EXTENDED"]
            
        for generation in ["O", "R1", "R2"]:
            for outcome in outcomes:
                for proximity in proximities:
                    combo_id = f"{generation}:{signal_type}:{proximity}:{outcome}"
                    combinations.append(combo_id)
                    
        return combinations
```

---

## 4. Automated Parameter Set Generation

### 4.1 Template-Based Generation

```python
class IndicatorParameterGenerator:
    def __init__(self):
        self.base_templates = INDICATOR_DEFAULTS
        
    def generate_parameter_set(self, indicator_name: str, status: IndicatorStatus) -> dict:
        """Generate parameter set for new indicator"""
        base_params = self.base_templates[status.value.upper()].copy()
        
        # Add indicator-specific parameters
        indicator_params = self._get_indicator_specific_params(indicator_name)
        base_params.update(indicator_params)
        
        # Generate unique parameter set ID
        base_params["parameter_set_id"] = f"PS-{status.value[:3]}-{indicator_name.lower()}-{int(time.time())}"
        base_params["name"] = f"{status.value.title()} {indicator_name}"
        base_params["indicator_source"] = indicator_name
        base_params["status"] = status.value
        base_params["created_at"] = datetime.utcnow().isoformat()
        
        return base_params
        
    def _get_indicator_specific_params(self, indicator_name: str) -> dict:
        """Get indicator-specific parameter overrides"""
        indicator_configs = {
            "percent_change": {
                "window_minutes": [15, 60, 240],  # 15m, 1h, 4h windows
                "threshold_percent": 0.5,         # 0.5% minimum change
                "use_log_returns": True
            },
            "currency_strength": {
                "normalization": "zscore",
                "equal_weights": True,
                "strength_threshold": 2.0
            },
            "rsi_divergence": {
                "rsi_period": 14,
                "divergence_bars": 5,
                "rsi_overbought": 70,
                "rsi_oversold": 30
            }
        }
        
        return indicator_configs.get(indicator_name.lower(), {})
```

### 4.2 Matrix Mapping Generation

```python
def generate_matrix_mappings(signal_type: str, status: IndicatorStatus):
    """Generate matrix mappings for new indicator"""
    mappings = []
    
    # Conservative decision rules based on status
    if status == IndicatorStatus.EXPERIMENTAL:
        default_decisions = {
            "WIN": "NO_REENTRY",      # No reentry on wins (take profit and exit)
            "LOSS": "END_TRADING",    # No reentry on losses (conservative)
            "BE": "END_TRADING"       # No reentry on breakeven
        }
    elif status == IndicatorStatus.TESTING:
        default_decisions = {
            "WIN": "SAME_TRADE",      # Same trade on wins
            "LOSS": "NO_REENTRY",     # No reentry on losses
            "BE": "SAME_TRADE"        # Same trade on breakeven
        }
    else:  # VALIDATED or PRODUCTION
        default_decisions = {
            "WIN": "SAME_TRADE",      # Continue winning strategy
            "LOSS": "REVERSE",        # Reverse on losses
            "BE": "INCREASE_SIZE"     # Increase size on breakeven
        }
        
    # Generate mappings
    for combo_id in get_combinations_for_signal(signal_type):
        outcome = extract_outcome_from_combo(combo_id)
        decision = default_decisions.get(outcome, "END_TRADING")
        
        mapping = {
            "combination_id": combo_id,
            "parameter_set_id": get_parameter_set_id_for_status(status),
            "decision": decision,
            "confidence_multiplier": get_confidence_for_status(status),
            "enabled": True,
            "notes": f"Auto-generated for {status.value} indicator"
        }
        mappings.append(mapping)
        
    return mappings
```

---

## 5. Safety Mechanisms and Monitoring

### 5.1 Automated Safety Checks

```python
class IndicatorSafetyMonitor:
    def __init__(self):
        self.performance_tracker = {}
        self.safety_limits = {
            "EXPERIMENTAL": {
                "max_daily_loss": 0.5,      # 0.5% max daily loss
                "max_consecutive_losses": 3,
                "min_win_rate": 0.3,        # 30% minimum win rate
                "max_drawdown": 1.0         # 1% max drawdown
            },
            "TESTING": {
                "max_daily_loss": 1.0,
                "max_consecutive_losses": 5,
                "min_win_rate": 0.4,
                "max_drawdown": 2.0
            }
        }
        
    def check_indicator_safety(self, indicator_name: str, status: IndicatorStatus):
        """Monitor indicator performance and safety"""
        performance = self.performance_tracker.get(indicator_name, {})
        limits = self.safety_limits.get(status.value.upper(), {})
        
        violations = []
        
        # Check daily loss
        if performance.get("daily_loss", 0) > limits.get("max_daily_loss", 999):
            violations.append("DAILY_LOSS_EXCEEDED")
            
        # Check consecutive losses
        if performance.get("consecutive_losses", 0) > limits.get("max_consecutive_losses", 999):
            violations.append("CONSECUTIVE_LOSSES_EXCEEDED")
            
        # Check win rate
        if performance.get("win_rate", 1.0) < limits.get("min_win_rate", 0):
            violations.append("WIN_RATE_TOO_LOW")
            
        # Check drawdown
        if performance.get("drawdown", 0) > limits.get("max_drawdown", 999):
            violations.append("DRAWDOWN_EXCEEDED")
            
        if violations:
            self._handle_safety_violations(indicator_name, violations)
            
    def _handle_safety_violations(self, indicator_name: str, violations: list):
        """Handle safety violations"""
        # Immediate actions
        self._disable_indicator_temporarily(indicator_name)
        self._send_safety_alert(indicator_name, violations)
        
        # Log for review
        self._log_safety_violation(indicator_name, violations)
```

### 5.2 Performance-Based Promotion

```python
class IndicatorPromotionManager:
    def __init__(self):
        self.promotion_criteria = {
            "EXPERIMENTAL_TO_TESTING": {
                "min_trades": 30,
                "min_days": 30,
                "max_loss_rate": 0.6,      # Max 60% loss rate
                "no_safety_violations": True
            },
            "TESTING_TO_VALIDATED": {
                "min_trades": 100,
                "min_days": 60,
                "min_win_rate": 0.45,      # 45% win rate
                "min_sharpe": 0.5,         # Positive risk-adjusted returns
                "max_drawdown": 2.0        # 2% max drawdown
            },
            "VALIDATED_TO_PRODUCTION": {
                "min_trades": 200,
                "min_days": 90,
                "min_win_rate": 0.5,       # 50% win rate
                "min_sharpe": 1.0,         # Good risk-adjusted returns
                "max_drawdown": 2.0,
                "manual_approval": True     # Requires manual review
            }
        }
        
    def evaluate_for_promotion(self, indicator_name: str, current_status: IndicatorStatus):
        """Evaluate if indicator is ready for promotion"""
        performance = self._get_indicator_performance(indicator_name)
        next_status = self._get_next_status(current_status)
        
        if not next_status:
            return False, "Already at highest status"
            
        criteria_key = f"{current_status.value.upper()}_TO_{next_status.value.upper()}"
        criteria = self.promotion_criteria.get(criteria_key, {})
        
        # Check all criteria
        results = self._check_promotion_criteria(performance, criteria)
        
        if all(results.values()):
            return True, f"Ready for promotion to {next_status.value}"
        else:
            failed_criteria = [k for k, v in results.items() if not v]
            return False, f"Failed criteria: {', '.join(failed_criteria)}"
```

---

## 6. Integration Workflow

### 6.1 New Indicator Registration Process

```python
def register_new_indicator_workflow(indicator_class, indicator_name: str):
    """Complete workflow for registering a new indicator"""
    
    # Step 1: Validate indicator implementation
    validator = IndicatorValidator()
    validation_result = validator.validate_indicator(indicator_class)
    if not validation_result.is_valid:
        raise ValueError(f"Indicator validation failed: {validation_result.errors}")
    
    # Step 2: Register with EXPERIMENTAL status
    status = IndicatorStatus.EXPERIMENTAL
    indicator_registry.register_indicator(indicator_class, status)
    
    # Step 3: Generate conservative parameter sets
    param_generator = IndicatorParameterGenerator()
    parameter_sets = param_generator.generate_parameter_set(indicator_name, status)
    
    # Step 4: Create matrix combinations
    matrix_manager = DynamicMatrixManager()
    matrix_manager.register_new_indicator(indicator_name, status)
    
    # Step 5: Set up monitoring
    safety_monitor = IndicatorSafetyMonitor()
    safety_monitor.register_indicator(indicator_name, status)
    
    # Step 6: Enable in limited mode
    trading_engine.enable_indicator(indicator_name, limited_mode=True)
    
    # Step 7: Log registration
    audit_logger.log_indicator_registration(indicator_name, status, parameter_sets)
    
    return {
        "status": "SUCCESS",
        "indicator_name": indicator_name,
        "initial_status": status.value,
        "parameter_sets_created": len(parameter_sets),
        "matrix_combinations": len(matrix_manager.dynamic_combinations)
    }
```

### 6.2 Configuration Management

```yaml
# indicator_integration_config.yaml
new_indicator_defaults:
  initial_status: "experimental"
  auto_enable: false
  require_manual_approval: true
  
safety_monitoring:
  check_interval_minutes: 15
  alert_thresholds:
    experimental:
      max_daily_loss: 0.5
      max_consecutive_losses: 3
    testing:
      max_daily_loss: 1.0
      max_consecutive_losses: 5
      
promotion_settings:
  auto_promote: false
  require_committee_review: true
  notification_emails:
    - "risk@trading.com"
    - "head_trader@trading.com"
    
parameter_generation:
  use_conservative_defaults: true
  inherit_from_similar_indicators: true
  apply_risk_scaling: true
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Implement IndicatorStatus enum and lifecycle management
- [ ] Create conservative parameter templates
- [ ] Build IndicatorParameterGenerator class
- [ ] Set up basic safety monitoring

### Phase 2: Matrix Integration (Week 3-4)
- [ ] Extend matrix system for dynamic indicators
- [ ] Implement DynamicMatrixManager
- [ ] Create automated mapping generation
- [ ] Build promotion evaluation system

### Phase 3: Safety & Monitoring (Week 5-6)
- [ ] Implement comprehensive safety checks
- [ ] Build performance tracking system
- [ ] Create automated promotion workflows
- [ ] Add real-time monitoring dashboard

### Phase 4: Production Ready (Week 7-8)
- [ ] Integration testing with existing system
- [ ] Performance optimization
- [ ] Documentation and training
- [ ] Deploy to staging environment

---

## 8. Example: Integrating Percent Change Indicator

```python
# Step-by-step example of integrating the new percent change indicator

# 1. Define the indicator with metadata
@indicator_metadata(
    name="percent_change",
    category=IndicatorCategory.PERCENT_CHANGE,
    description="Multi-window percentage change analysis using log returns",
    parameters={
        "windows_sec": [900, 3600, 14400, 28800, 43200, 86400],
        "threshold_percent": 0.5,
        "use_log_returns": True
    },
    output_fields=["15m", "1h", "4h", "8h", "12h", "24h"],
    time_windows=["15m", "1h", "4h", "8h", "12h", "24h"]
)
class PercentChangeIndicator(StandardIndicatorInterface):
    def calculate(self, price_data: Dict) -> Dict[str, Any]:
        # Implementation using the fast math from the document
        return self.get_windowed_log_returns(price_data)

# 2. Register the indicator (automatic with conservative defaults)
register_new_indicator_workflow(PercentChangeIndicator, "percent_change")

# 3. Generated parameter set (automatically created)
{
    "parameter_set_id": "PS-exp-percent_change-1693843200",
    "name": "Experimental Percent Change",
    "global_risk_percent": 0.5,        # Ultra-conservative
    "confidence_threshold": 0.85,       # High confidence required
    "stop_loss_pips": 15,
    "take_profit_pips": 30,
    "max_positions": 1,
    "cooldown_minutes": 60,
    "enabled_sessions": ["LONDON"],
    "risk_multiplier": 0.25,
    "signal_strength_required": 0.9,
    "window_minutes": [15, 60, 240],
    "threshold_percent": 0.5,
    "use_log_returns": True,
    "status": "experimental",
    "created_at": "2025-09-04T10:30:00Z"
}

# 4. Generated matrix combinations (limited for experimental)
combinations = [
    "O:EXP_PERCENT_CHANGE:LONG:WIN",
    "O:EXP_PERCENT_CHANGE:LONG:LOSS",
    "O:EXP_PERCENT_CHANGE:EXTENDED:WIN",
    "O:EXP_PERCENT_CHANGE:EXTENDED:LOSS",
    "R1:EXP_PERCENT_CHANGE:LONG:WIN",
    "R1:EXP_PERCENT_CHANGE:LONG:LOSS",
    # ... (16 total combinations vs 1008 for production indicators)
]

# 5. Conservative matrix mappings (automatically generated)
matrix_mappings = {
    "O:EXP_PERCENT_CHANGE:LONG:WIN": {
        "decision": "NO_REENTRY",     # Take profit and exit
        "parameter_set_id": "PS-exp-percent_change-1693843200",
        "confidence_multiplier": 0.5,  # Reduced confidence
        "enabled": True
    },
    "O:EXP_PERCENT_CHANGE:LONG:LOSS": {
        "decision": "END_TRADING",    # No reentry on loss
        "parameter_set_id": "PS-exp-percent_change-1693843200", 
        "confidence_multiplier": 0.5,
        "enabled": True
    }
    # ... other combinations with conservative settings
}
```

---

## Conclusion

This integration framework provides:

✅ **Safety First**: Conservative defaults minimize risk exposure  
✅ **Systematic Progression**: Clear pathway from experimental to production  
✅ **Automated Management**: Reduces manual configuration overhead  
✅ **Performance Validation**: Objective criteria for promotion decisions  
✅ **Risk Controls**: Multiple safety mechanisms and monitoring  
✅ **Matrix Compatibility**: Seamless integration with existing system  

The system ensures new indicators can be safely tested and validated while protecting the overall trading system performance.