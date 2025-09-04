#!/usr/bin/env python3
"""
HUEY_P Guardian System - Autonomous Monitoring & Self-Healing
Trading-Specific Implementation with Hysteresis and Circuit Breakers
"""

import asyncio
import json
import logging
import sqlite3
import time
import uuid
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import yaml
import win32serviceutil
import win32service
import win32event


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    RECOVERING = "recovering"
    CRITICAL = "critical"
    SAFE_MODE = "safe_mode"


class SystemState(Enum):
    HEALTHY = "Healthy"
    DEGRADED = "Degraded"
    RECOVERING = "Recovering"
    SAFE_MODE = "SafeMode"


@dataclass
class HealthMetric:
    name: str
    status: HealthStatus
    value: Any
    timestamp: datetime
    baseline: Optional[float] = None
    ema_window: int = 100
    consecutive_failures: int = 0
    consecutive_successes: int = 0


@dataclass 
class CommandEnvelope:
    cmd_seq: int
    idempotency_key: str
    op: str
    symbol: str
    parameters: Dict[str, Any]
    constraints: Dict[str, Any] = field(default_factory=dict)
    deadline_ts: str = ""
    trace_id: str = ""
    config_version: str = "guardian-1.0.0"
    
    def __post_init__(self):
        if not self.deadline_ts:
            self.deadline_ts = (datetime.utcnow() + timedelta(seconds=30)).isoformat()
        if not self.trace_id:
            self.trace_id = f"trc_{uuid.uuid4().hex[:8]}"
        if not self.idempotency_key:
            self.idempotency_key = f"cmd-{datetime.utcnow().isoformat()}-{uuid.uuid4().hex[:8]}"


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, 
                 half_open_probe_count: int = 1):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_probe_count = half_open_probe_count
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.probe_count = 0
        
    def call(self, func: Callable, *args, **kwargs):
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                self.probe_count = 0
            else:
                raise CircuitBreakerOpenException(f"Circuit breaker OPEN for {self.failure_count} failures")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        if self.state == "HALF_OPEN":
            self.probe_count += 1
            if self.probe_count >= self.half_open_probe_count:
                self.state = "CLOSED"
                self.failure_count = 0
        elif self.state == "CLOSED":
            self.failure_count = max(0, self.failure_count - 1)
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
        elif self.state == "HALF_OPEN":
            self.state = "OPEN"
    
    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time:
            time_since_failure = datetime.utcnow() - self.last_failure_time
            return time_since_failure.seconds >= self.recovery_timeout
        return False


class CircuitBreakerOpenException(Exception):
    pass


class HysteresisEvaluator:
    """Implements N-of-M logic with EMA baselines to prevent flapping"""
    
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.history = deque(maxlen=window_size)
        self.ema_baseline = None
        self.ema_alpha = 0.1  # Smoothing factor
        
    def update_baseline(self, value: float):
        if self.ema_baseline is None:
            self.ema_baseline = value
        else:
            self.ema_baseline = self.ema_alpha * value + (1 - self.ema_alpha) * self.ema_baseline
    
    def evaluate_threshold(self, value: float, threshold_multiplier: float = 1.5) -> bool:
        """Returns True if value breaches adaptive threshold"""
        if self.ema_baseline is None:
            return False
        
        adaptive_threshold = self.ema_baseline * threshold_multiplier
        return value > adaptive_threshold
    
    def evaluate_n_of_m(self, current_status: bool, promote_rule: str = "3_of_5", 
                       demote_rule: str = "2_of_3") -> Optional[bool]:
        """
        Evaluates N-of-M promotion/demotion rules
        Returns: True (promote), False (demote), None (no change)
        """
        self.history.append(current_status)
        
        if len(self.history) < 3:
            return None
        
        recent_failures = sum(1 for x in list(self.history)[-5:] if not x)
        recent_successes = sum(1 for x in list(self.history)[-3:] if x)
        
        # Parse rules (e.g., "3_of_5" -> 3 failures in last 5)
        promote_n, promote_m = map(int, promote_rule.split("_of_"))
        demote_n, demote_m = map(int, demote_rule.split("_of_"))
        
        # Promote to degraded/critical if enough failures
        if len(self.history) >= promote_m and recent_failures >= promote_n:
            return True
        
        # Demote to healthy if enough successes  
        if len(self.history) >= demote_m and recent_successes >= demote_n:
            return False
            
        return None


class GuardianHealthMonitor:
    """Trading-specific health monitoring with adaptive thresholds"""
    
    def __init__(self, config_path: str = "guardian_config.yaml"):
        self.config = self._load_config(config_path)
        self.health_metrics: Dict[str, HealthMetric] = {}
        self.hysteresis_evaluators: Dict[str, HysteresisEvaluator] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.system_state = SystemState.HEALTHY
        self.cmd_seq = 0
        self.processed_commands = set()  # For idempotency
        
        # Initialize evaluators and breakers
        for check in self.config['health_checks']:
            name = check['name']
            self.hysteresis_evaluators[name] = HysteresisEvaluator()
            
            # Per-symbol or system-wide circuit breakers
            if check.get('per_symbol', False):
                cb_config = self.config['circuit_breakers']['per_symbol']
            else:
                cb_config = self.config['circuit_breakers']['system_wide']
                
            self.circuit_breakers[name] = CircuitBreaker(
                failure_threshold=cb_config['failure_threshold'],
                recovery_timeout=self._parse_duration(cb_config['recovery_timeout']),
                half_open_probe_count=cb_config.get('half_open_probe_count', 1)
            )
    
    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration strings like '2m', '30s' to seconds"""
        if duration_str.endswith('s'):
            return int(duration_str[:-1])
        elif duration_str.endswith('m'):
            return int(duration_str[:-1]) * 60
        elif duration_str.endswith('h'):
            return int(duration_str[:-1]) * 3600
        return int(duration_str)
    
    async def continuous_monitoring_loop(self):
        """Main guardian monitoring loop"""
        logging.info("Guardian monitoring started")
        
        while True:
            try:
                # Execute all health checks
                health_results = await self._execute_health_checks()
                
                # Update system state based on results
                new_state = self._evaluate_system_state(health_results)
                if new_state != self.system_state:
                    await self._handle_state_transition(self.system_state, new_state)
                    self.system_state = new_state
                
                # Check for alerts and trigger remediation
                alerts = self._evaluate_alerts(health_results)
                for alert in alerts:
                    await self._handle_alert(alert)
                
                await asyncio.sleep(10)  # Main loop interval
                
            except Exception as e:
                logging.error(f"Guardian monitoring error: {e}")
                await asyncio.sleep(30)  # Longer wait on error
    
    async def _execute_health_checks(self) -> Dict[str, HealthMetric]:
        """Execute all configured health checks"""
        results = {}
        
        for check_config in self.config['health_checks']:
            check_name = check_config['name']
            
            try:
                # Execute health check with circuit breaker protection
                check_result = await self.circuit_breakers[check_name].call(
                    self._execute_single_health_check, check_config
                )
                
                # Update hysteresis evaluator
                evaluator = self.hysteresis_evaluators[check_name]
                evaluator.update_baseline(check_result.value)
                
                # Apply hysteresis logic
                threshold_breach = evaluator.evaluate_threshold(
                    check_result.value, 
                    check_config.get('thresholds', {}).get('multiplier', 1.5)
                )
                
                n_of_m_result = evaluator.evaluate_n_of_m(
                    not threshold_breach,  # Success = no breach
                    check_config.get('hysteresis', {}).get('promote_after', '3_of_5'),
                    check_config.get('hysteresis', {}).get('demote_after', '2_of_3')
                )
                
                # Update health status based on hysteresis
                if n_of_m_result is True:  # Promote to degraded
                    check_result.status = HealthStatus.DEGRADED
                elif n_of_m_result is False:  # Demote to healthy
                    check_result.status = HealthStatus.HEALTHY
                
                results[check_name] = check_result
                
            except CircuitBreakerOpenException:
                # Circuit breaker is open - mark as critical
                results[check_name] = HealthMetric(
                    name=check_name,
                    status=HealthStatus.CRITICAL,
                    value=None,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logging.error(f"Health check {check_name} failed: {e}")
                results[check_name] = HealthMetric(
                    name=check_name,
                    status=HealthStatus.CRITICAL,
                    value=str(e),
                    timestamp=datetime.utcnow()
                )
        
        return results
    
    async def _execute_single_health_check(self, config: Dict) -> HealthMetric:
        """Execute individual health check based on type"""
        check_type = config['type']
        check_name = config['name']
        
        if check_type == "mt4_ea_heartbeat":
            return await self._check_ea_heartbeat(config)
        elif check_type == "bridge_latency":
            return await self._check_bridge_latency(config)
        elif check_type == "sqlite_check":
            return await self._check_sqlite_health(config)
        elif check_type == "system_metric":
            return await self._check_system_metric(config)
        elif check_type == "risk_metric":
            return await self._check_risk_exposure(config)
        elif check_type == "broker_sync":
            return await self._check_broker_reconciliation(config)
        else:
            raise ValueError(f"Unknown health check type: {check_type}")
    
    async def _check_ea_heartbeat(self, config: Dict) -> HealthMetric:
        """Check EA heartbeat responsiveness"""
        start_time = time.time()
        
        try:
            # Send heartbeat request to EA
            heartbeat_cmd = CommandEnvelope(
                cmd_seq=self._next_cmd_seq(),
                op="HEARTBEAT_REQUEST",
                symbol=config.get('symbol', '*'),
                parameters={}
            )
            
            response = await self._send_ea_command(heartbeat_cmd, timeout=config['timeout'])
            latency_ms = (time.time() - start_time) * 1000
            
            if latency_ms > 2000:  # Degraded if > 2s
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return HealthMetric(
                name=config['name'],
                status=status,
                value=latency_ms,
                timestamp=datetime.utcnow()
            )
            
        except asyncio.TimeoutError:
            return HealthMetric(
                name=config['name'],
                status=HealthStatus.CRITICAL,
                value=float('inf'),
                timestamp=datetime.utcnow()
            )
    
    async def _check_bridge_latency(self, config: Dict) -> HealthMetric:
        """Check communication bridge performance"""
        transport = config['transport']
        start_time = time.time()
        
        try:
            if transport == "socket":
                latency = await self._test_socket_latency()
            elif transport == "csv":
                latency = await self._test_csv_latency()
            else:
                raise ValueError(f"Unknown transport: {transport}")
            
            # Determine status based on adaptive thresholds
            evaluator = self.hysteresis_evaluators[config['name']]
            if evaluator.ema_baseline:
                warn_threshold = evaluator.ema_baseline * 1.5
                crit_threshold = config['thresholds'].get('crit_ms', 500)
            else:
                warn_threshold = 100
                crit_threshold = 500
            
            if latency > crit_threshold:
                status = HealthStatus.CRITICAL
            elif latency > warn_threshold:
                status = HealthStatus.DEGRADED  
            else:
                status = HealthStatus.HEALTHY
            
            return HealthMetric(
                name=config['name'],
                status=status,
                value=latency,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return HealthMetric(
                name=config['name'],
                status=HealthStatus.CRITICAL,
                value=float('inf'),
                timestamp=datetime.utcnow()
            )
    
    async def _check_sqlite_health(self, config: Dict) -> HealthMetric:
        """Check SQLite database health and integrity"""
        db_path = config['db_path']
        
        try:
            with sqlite3.connect(db_path) as conn:
                # Check WAL mode
                cursor = conn.cursor()
                cursor.execute("PRAGMA journal_mode")
                journal_mode = cursor.fetchone()[0]
                
                if journal_mode.upper() != 'WAL':
                    return HealthMetric(
                        name=config['name'],
                        status=HealthStatus.DEGRADED,
                        value=f"journal_mode={journal_mode}",
                        timestamp=datetime.utcnow()
                    )
                
                # Integrity check
                cursor.execute("PRAGMA integrity_check(10)")
                integrity_result = cursor.fetchall()
                
                if len(integrity_result) == 1 and integrity_result[0][0] == 'ok':
                    status = HealthStatus.HEALTHY
                    value = "ok"
                else:
                    status = HealthStatus.CRITICAL
                    value = f"integrity_errors={len(integrity_result)}"
                
                return HealthMetric(
                    name=config['name'],
                    status=status,
                    value=value,
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            return HealthMetric(
                name=config['name'],
                status=HealthStatus.CRITICAL,
                value=str(e),
                timestamp=datetime.utcnow()
            )
    
    async def _check_risk_exposure(self, config: Dict) -> HealthMetric:
        """Monitor risk exposure across all positions"""
        try:
            # Get current positions and calculate risk metrics
            positions = await self._get_current_positions()
            
            total_risk_pct = sum(pos.get('risk_percent', 0) for pos in positions)
            max_single_risk = max((pos.get('risk_percent', 0) for pos in positions), default=0)
            account_drawdown = await self._get_account_drawdown()
            
            # Check risk limits
            risk_breach = (
                max_single_risk > config['max_per_trade_pct'] or
                account_drawdown > config['max_drawdown_pct'] or
                total_risk_pct > config.get('max_total_risk_pct', 10)
            )
            
            if risk_breach:
                status = HealthStatus.CRITICAL
            elif max_single_risk > config['max_per_trade_pct'] * 0.8:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return HealthMetric(
                name=config['name'],
                status=status,
                value={
                    'total_risk_pct': total_risk_pct,
                    'max_single_risk': max_single_risk,
                    'account_drawdown': account_drawdown
                },
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return HealthMetric(
                name=config['name'],
                status=HealthStatus.CRITICAL,
                value=str(e),
                timestamp=datetime.utcnow()
            )
    
    def _evaluate_system_state(self, health_results: Dict[str, HealthMetric]) -> SystemState:
        """Evaluate overall system state based on health metrics"""
        critical_count = sum(1 for metric in health_results.values() 
                           if metric.status == HealthStatus.CRITICAL)
        degraded_count = sum(1 for metric in health_results.values() 
                           if metric.status == HealthStatus.DEGRADED)
        
        if critical_count > 0:
            return SystemState.SAFE_MODE
        elif degraded_count > 2:  # More than 2 degraded systems
            return SystemState.DEGRADED
        elif self.system_state == SystemState.RECOVERING:
            # Stay in recovering until all systems are healthy
            if degraded_count == 0 and critical_count == 0:
                return SystemState.HEALTHY
            else:
                return SystemState.RECOVERING
        else:
            return SystemState.HEALTHY
    
    async def _handle_alert(self, alert: Dict):
        """Handle alert by triggering appropriate remediation"""
        alert_name = alert['name']
        remediation = alert.get('auto_remediation')
        
        if not remediation:
            logging.warning(f"No remediation defined for alert: {alert_name}")
            return
        
        logging.info(f"Triggering remediation: {remediation} for alert: {alert_name}")
        
        # Set system to recovering state
        self.system_state = SystemState.RECOVERING
        
        try:
            success = await self._execute_remediation_playbook(remediation, alert)
            if success:
                logging.info(f"Remediation {remediation} completed successfully")
            else:
                logging.error(f"Remediation {remediation} failed")
                if alert.get('escalate_immediately'):
                    await self._escalate_to_human(alert, "Remediation failed")
        except Exception as e:
            logging.error(f"Remediation {remediation} error: {e}")
            await self._escalate_to_human(alert, str(e))
    
    async def _execute_remediation_playbook(self, playbook_name: str, alert: Dict) -> bool:
        """Execute automated remediation playbook"""
        playbook = self.config['remediation_playbooks'].get(playbook_name)
        if not playbook:
            logging.error(f"Unknown playbook: {playbook_name}")
            return False
        
        max_duration = self._parse_duration(playbook.get('max_duration', '5m'))
        start_time = time.time()
        
        try:
            for step in playbook['steps']:
                if time.time() - start_time > max_duration:
                    logging.error(f"Playbook {playbook_name} exceeded max duration")
                    return False
                
                step_name = step['name']
                action = step['action']
                timeout = self._parse_duration(step.get('timeout', '30s'))
                
                logging.info(f"Executing playbook step: {step_name}")
                
                success = await self._execute_remediation_action(action, step, timeout)
                if not success and not step.get('continue_on_failure', False):
                    logging.error(f"Playbook step {step_name} failed")
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"Playbook {playbook_name} execution error: {e}")
            return False
    
    async def _execute_remediation_action(self, action: str, step: Dict, timeout: int) -> bool:
        """Execute individual remediation action"""
        try:
            if action == "pause_new_commands":
                return await self._pause_new_commands()
            elif action == "reset_all_communication_channels":
                return await self._reset_bridges()
            elif action == "restart_ea_via_dde":
                return await self._restart_ea()
            elif action == "reconcile_with_broker":
                return await self._reconcile_with_broker()
            elif action == "activate_csv_bridge":
                return await self._switch_to_csv_bridge()
            elif action == "close_positions_graceful":
                return await self._close_positions_graceful(step.get('max_slippage_pips', 5))
            elif action == "require_manual_relatch":
                return await self._engage_manual_latch(step.get('conditions', []))
            elif action == "emergency_state_checkpoint":
                return await self._create_emergency_checkpoint()
            elif action == "send_critical_alert":
                return await self._send_critical_alert(step.get('channels', ['email']))
            else:
                logging.error(f"Unknown remediation action: {action}")
                return False
        except Exception as e:
            logging.error(f"Remediation action {action} failed: {e}")
            return False
    
    def _next_cmd_seq(self) -> int:
        """Generate next command sequence number"""
        self.cmd_seq += 1
        return self.cmd_seq
    
    async def _send_ea_command(self, command: CommandEnvelope, timeout: float) -> Dict:
        """Send command to EA with idempotency checking"""
        if command.idempotency_key in self.processed_commands:
            logging.warning(f"Duplicate command ignored: {command.idempotency_key}")
            return {"status": "duplicate"}
        
        self.processed_commands.add(command.idempotency_key)
        
        # Implement actual EA communication here
        # This would use your socket bridge or CSV bridge
        await asyncio.sleep(0.1)  # Simulate EA communication
        return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
    
    # Additional helper methods would be implemented here...
    # _test_socket_latency, _test_csv_latency, _get_current_positions, etc.


class GuardianService(win32serviceutil.ServiceFramework):
    """Windows service wrapper for Guardian system"""
    
    _svc_name_ = "HueyPGuardian"
    _svc_display_name_ = "HUEY_P Guardian Monitoring Service"
    _svc_description_ = "Autonomous monitoring and self-healing for HUEY_P trading system"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.guardian = None
    
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
    
    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('guardian.log'),
                logging.handlers.RotatingFileHandler(
                    'guardian.log', maxBytes=10*1024*1024, backupCount=5
                )
            ]
        )
        
        # Start Guardian
        self.guardian = GuardianHealthMonitor()
        
        # Run async loop
        asyncio.run(self._run_guardian())
    
    async def _run_guardian(self):
        """Run guardian monitoring loop"""
        try:
            await self.guardian.continuous_monitoring_loop()
        except Exception as e:
            logging.critical(f"Guardian service crashed: {e}")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Run as service
        win32serviceutil.HandleCommandLine(GuardianService)
    else:
        # Run directly for testing
        guardian = GuardianHealthMonitor()
        asyncio.run(guardian.continuous_monitoring_loop())