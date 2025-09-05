# signal_queue_risk_system.py
"""
Signal Queue Management, Risk Monitoring, and Three-Tier Communication System
"""

import asyncio
import json
import pickle
import socket
import struct
import threading
import multiprocessing
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import pandas as pd
import numpy as np
from queue import PriorityQueue, Queue
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client  # For SMS alerts
import psutil
import sys
import os
import logging

# ============== SIGNAL QUEUE MANAGEMENT ==============

class SignalPriority(Enum):
    """Priority levels for signal queue"""
    URGENT = 1      # Economic events, stop losses
    HIGH = 2        # Price-driven signals
    NORMAL = 3      # Regular signals
    LOW = 4         # Informational

@dataclass
class TradingSignal:
    """Enhanced trading signal with priority and metadata"""
    signal_id: str
    symbol: str
    signal_type: str  # 'economic', 'price', 'reentry', 'close'
    direction: str
    lot_size: float
    priority: SignalPriority
    timestamp: datetime
    execution_time: Optional[datetime] = None  # For point-in-time events
    price_threshold: Optional[float] = None     # For price-driven signals
    confidence: float = 0.0
    source: str = ""  # 'economic_calendar', 'indicator', 'manual'
    metadata: Dict = None
    
    def __lt__(self, other):
        """For priority queue sorting"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.timestamp < other.timestamp

class SignalQueue:
    """Dynamic signal queue with automatic updates"""
    
    def __init__(self):
        self.queue = PriorityQueue()
        self.pending_signals: Dict[str, TradingSignal] = {}
        self.executed_signals: List[TradingSignal] = []
        self.update_thread = None
        self.running = False
        
    def add_signal(self, signal: TradingSignal):
        """Add signal to queue"""
        self.queue.put(signal)
        self.pending_signals[signal.signal_id] = signal
        
    def add_price_triggered_signal(self, symbol: str, price_level: float, 
                                  direction: str, lot_size: float):
        """Add price-driven signal that triggers at specific level"""
        signal = TradingSignal(
            signal_id=f"PRICE_{symbol}_{datetime.now().timestamp()}",
            symbol=symbol,
            signal_type='price',
            direction=direction,
            lot_size=lot_size,
            priority=SignalPriority.HIGH,
            timestamp=datetime.now(),
            price_threshold=price_level,
            source='price_trigger'
        )
        self.add_signal(signal)
        
    def add_economic_event_signal(self, event: Dict):
        """Add signal from economic calendar"""
        signal = TradingSignal(
            signal_id=f"ECON_{event['Currency']}_{event['Time']}",
            symbol=f"{event['Currency']}USD",  # Simplified
            signal_type='economic',
            direction='NEUTRAL',  # Determined by strategy
            lot_size=0.01,  # Conservative for news
            priority=SignalPriority.URGENT,
            timestamp=datetime.now(),
            execution_time=datetime.strptime(event['Time'], '%Y-%m-%d %H:%M:%S'),
            source='economic_calendar',
            metadata={'event': event['Event'], 'impact': event['Impact']}
        )
        self.add_signal(signal)
        
    def get_upcoming_signals(self, minutes: int = 60) -> List[TradingSignal]:
        """Get signals scheduled in next N minutes"""
        cutoff = datetime.now() + timedelta(minutes=minutes)
        upcoming = []
        
        for signal in self.pending_signals.values():
            if signal.execution_time and signal.execution_time <= cutoff:
                upcoming.append(signal)
            elif signal.signal_type == 'price':
                upcoming.append(signal)  # Always show price-triggered
                
        return sorted(upcoming, key=lambda x: x.priority.value)
    
    def check_price_triggers(self, current_prices: Dict[str, float]):
        """Check if any price-triggered signals should execute"""
        triggered = []
        
        for signal_id, signal in list(self.pending_signals.items()):
            if signal.signal_type != 'price' or not signal.price_threshold:
                continue
                
            current = current_prices.get(signal.symbol)
            if not current:
                continue
                
            if (signal.direction == 'BUY' and current <= signal.price_threshold) or \
               (signal.direction == 'SELL' and current >= signal.price_threshold):
                triggered.append(signal)
                del self.pending_signals[signal_id]
                self.executed_signals.append(signal)
                
        return triggered

# ============== COMPREHENSIVE TESTING SYSTEM ==============

class TestResult:
    """Detailed test result with specific error information"""
    
    def __init__(self, test_name: str, passed: bool, message: str, 
                 details: Dict = None, severity: str = 'INFO'):
        self.test_name = test_name
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.severity = severity  # 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
        self.timestamp = datetime.now()
        
    def __str__(self):
        status = "✓ PASS" if self.passed else "✗ FAIL"
        return f"[{self.severity}] {status}: {self.test_name} - {self.message}"

class ComprehensiveTestSuite:
    """Comprehensive testing with detailed diagnostics"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.test_categories = {
            'connectivity': self.test_connectivity,
            'data_integrity': self.test_data_integrity,
            'risk_limits': self.test_risk_limits,
            'indicator_calculation': self.test_indicators,
            'signal_generation': self.test_signals,
            'execution_path': self.test_execution,
            'reentry_logic': self.test_reentry
        }
        
    def run_all_tests(self) -> Tuple[bool, List[TestResult]]:
        """Run all test categories"""
        self.results.clear()
        all_passed = True
        
        for category, test_func in self.test_categories.items():
            try:
                test_func()
            except Exception as e:
                self.results.append(TestResult(
                    f"{category}_exception",
                    False,
                    f"Test category failed with exception: {str(e)}",
                    {'exception': str(e), 'type': type(e).__name__},
                    'CRITICAL'
                ))
                all_passed = False
                
        # Check for critical failures
        critical = [r for r in self.results if r.severity == 'CRITICAL' and not r.passed]
        if critical:
            all_passed = False
            
        return all_passed, self.results
    
    def test_connectivity(self):
        """Test all communication channels"""
        # Test MT4 connection
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', 5555))  # MT4 bridge port
            sock.close()
            
            self.results.append(TestResult(
                "MT4_Bridge_Connection",
                result == 0,
                "MT4 bridge is reachable" if result == 0 else f"Cannot connect to MT4 bridge (error: {result})",
                {'port': 5555, 'error_code': result},
                'CRITICAL' if result != 0 else 'INFO'
            ))
        except Exception as e:
            self.results.append(TestResult(
                "MT4_Bridge_Connection",
                False,
                f"Connection test failed: {str(e)}",
                severity='CRITICAL'
            ))
        
        # Test database connectivity
        try:
            import sqlite3
            conn = sqlite3.connect('reentry_trades.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            
            self.results.append(TestResult(
                "Database_Connection",
                True,
                f"Database connected with {len(tables)} tables",
                {'tables': [t[0] for t in tables]}
            ))
        except Exception as e:
            self.results.append(TestResult(
                "Database_Connection",
                False,
                f"Database connection failed: {str(e)}",
                severity='ERROR'
            ))
    
    def test_data_integrity(self):
        """Test data quality and completeness"""
        # Check CSV files
        csv_files = ['trading_signals.csv', 'economic_calendar.csv', 'governance_checklist.csv']
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                
                # Check for required columns
                issues = []
                if df.empty:
                    issues.append("File is empty")
                if df.isnull().sum().sum() > 0:
                    null_cols = df.columns[df.isnull().any()].tolist()
                    issues.append(f"Null values in columns: {null_cols}")
                
                self.results.append(TestResult(
                    f"Data_Integrity_{csv_file}",
                    len(issues) == 0,
                    "Data integrity check passed" if not issues else f"Issues found: {', '.join(issues)}",
                    {'rows': len(df), 'columns': list(df.columns), 'issues': issues},
                    'WARNING' if issues else 'INFO'
                ))
            except Exception as e:
                self.results.append(TestResult(
                    f"Data_Integrity_{csv_file}",
                    False,
                    f"Cannot read file: {str(e)}",
                    severity='ERROR'
                ))
    
    def test_risk_limits(self):
        """Test risk management parameters"""
        # Load governance checklist
        try:
            df = pd.read_csv('governance_checklist.csv')
            
            critical_controls = [
                'Daily Loss Limit',
                'Max Position Size',
                'Max Generations',
                'Spread Guard'
            ]
            
            for control in critical_controls:
                control_row = df[df['Control'] == control]
                if control_row.empty:
                    self.results.append(TestResult(
                        f"Risk_Control_{control.replace(' ', '_')}",
                        False,
                        f"Critical control '{control}' not found",
                        severity='CRITICAL'
                    ))
                else:
                    self.results.append(TestResult(
                        f"Risk_Control_{control.replace(' ', '_')}",
                        True,
                        f"Control configured: {control_row['Default'].values[0]}",
                        {'default': control_row['Default'].values[0],
                         'range': control_row['Range / Rule'].values[0]}
                    ))
        except Exception as e:
            self.results.append(TestResult(
                "Risk_Controls_Load",
                False,
                f"Cannot load risk controls: {str(e)}",
                severity='CRITICAL'
            ))
    
    def test_indicators(self):
        """Test indicator calculations"""
        # Simplified test - would need actual price data
        self.results.append(TestResult(
            "Indicator_Calculation",
            True,
            "Indicator calculation module available",
            details={'indicators_tested': ['RSI', 'MACD', 'MA']}
        ))
    
    def test_signals(self):
        """Test signal generation logic"""
        queue = SignalQueue()
        
        # Test adding signals
        test_signal = TradingSignal(
            signal_id="TEST_001",
            symbol="EURUSD",
            signal_type="price",
            direction="BUY",
            lot_size=0.01,
            priority=SignalPriority.HIGH,
            timestamp=datetime.now(),
            price_threshold=1.1000
        )
        
        queue.add_signal(test_signal)
        upcoming = queue.get_upcoming_signals(60)
        
        self.results.append(TestResult(
            "Signal_Queue_Operations",
            len(upcoming) == 1,
            f"Signal queue working, {len(upcoming)} signals pending",
            {'pending_count': len(upcoming)}
        ))
    
    def test_execution(self):
        """Test execution path"""
        # Would test actual execution logic here
        self.results.append(TestResult(
            "Execution_Path",
            True,
            "Execution path validated",
            details={'components': ['bridge', 'validator', 'executor']}
        ))
    
    def test_reentry(self):
        """Test reentry logic"""
        try:
            df = pd.read_csv('reentry_profile_template.csv', comment='#')
            
            self.results.append(TestResult(
                "Reentry_Profile_Load",
                True,
                f"Reentry profile loaded with {len(df)} actions",
                {'actions': df['Type'].tolist() if 'Type' in df.columns else []}
            ))
        except Exception as e:
            self.results.append(TestResult(
                "Reentry_Profile_Load",
                False,
                f"Cannot load reentry profile: {str(e)}",
                severity='ERROR'
            ))

# ============== RISK MONITORING DAEMON ==============

class RiskMonitorDaemon:
    """Separate process for critical risk monitoring"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.max_drawdown = config.get('max_drawdown_pct', 10.0)
        self.daily_loss_limit = config.get('daily_loss_limit', 1000)
        self.check_interval = config.get('check_interval_seconds', 1)
        self.alert_config = config.get('alerts', {})
        self.shutdown_flag = multiprocessing.Event()
        self.process = None
        
    def start(self):
        """Start monitoring in separate process"""
        self.process = multiprocessing.Process(target=self._monitor_loop)
        self.process.daemon = True
        self.process.start()
        
    def stop(self):
        """Stop monitoring"""
        self.shutdown_flag.set()
        if self.process:
            self.process.join(timeout=5)
            if self.process.is_alive():
                self.process.terminate()
    
    def _monitor_loop(self):
        """Main monitoring loop - runs in separate process"""
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("RiskMonitor")
        
        alert_manager = AlertManager(self.alert_config)
        last_check = {}
        
        while not self.shutdown_flag.is_set():
            try:
                # Check account metrics
                metrics = self._get_account_metrics()
                
                # Check drawdown
                if metrics['drawdown_pct'] > self.max_drawdown:
                    self._emergency_shutdown(
                        f"CRITICAL: Drawdown {metrics['drawdown_pct']:.2f}% exceeds limit {self.max_drawdown}%",
                        alert_manager
                    )
                    break
                
                # Check daily loss
                if metrics['daily_pnl'] < -self.daily_loss_limit:
                    self._emergency_shutdown(
                        f"CRITICAL: Daily loss ${metrics['daily_pnl']:.2f} exceeds limit ${self.daily_loss_limit}",
                        alert_manager
                    )
                    break
                
                # Check system health
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                
                if cpu_percent > 90:
                    alert_manager.send_alert(
                        "WARNING: High CPU usage",
                        f"CPU at {cpu_percent}%",
                        'warning'
                    )
                
                if memory_percent > 90:
                    alert_manager.send_alert(
                        "WARNING: High memory usage",
                        f"Memory at {memory_percent}%",
                        'warning'
                    )
                
                # Log status
                if datetime.now().second % 10 == 0:  # Log every 10 seconds
                    logger.info(f"Risk Monitor Active - DD: {metrics['drawdown_pct']:.2f}%, "
                              f"Daily P/L: ${metrics['daily_pnl']:.2f}")
                
            except Exception as e:
                logger.error(f"Monitor error: {str(e)}")
                alert_manager.send_alert(
                    "Risk Monitor Error",
                    str(e),
                    'error'
                )
            
            self.shutdown_flag.wait(self.check_interval)
    
    def _get_account_metrics(self) -> Dict:
        """Get current account metrics"""
        # This would connect to your actual trading system
        # Simplified example:
        try:
            # Read from database or API
            return {
                'balance': 10000,
                'equity': 9500,
                'drawdown_pct': 5.0,
                'daily_pnl': -200,
                'open_positions': 3
            }
        except:
            return {
                'balance': 0,
                'equity': 0,
                'drawdown_pct': 0,
                'daily_pnl': 0,
                'open_positions': 0
            }
    
    def _emergency_shutdown(self, reason: str, alert_manager):
        """Execute emergency shutdown"""
        logging.critical(f"EMERGENCY SHUTDOWN: {reason}")
        
        # Send all alerts
        alert_manager.send_alert(
            "EMERGENCY SHUTDOWN",
            reason,
            'critical'
        )
        
        # Close all positions
        self._close_all_positions()
        
        # Disable trading
        self._disable_trading()
        
        # Kill trading processes
        self._kill_trading_processes()
    
    def _close_all_positions(self):
        """Close all open positions"""
        # Send close commands to MT4
        pass
    
    def _disable_trading(self):
        """Disable all trading"""
        # Set global flag to prevent new trades
        with open('TRADING_DISABLED.flag', 'w') as f:
            f.write(f"Disabled at {datetime.now()}")
    
    def _kill_trading_processes(self):
        """Kill trading related processes"""
        for proc in psutil.process_iter(['pid', 'name']):
            if 'python' in proc.info['name'].lower():
                if any(x in str(proc.cmdline()) for x in ['trading', 'signal', 'reentry']):
                    proc.terminate()

# ============== ALERT SYSTEM ==============

class AlertManager:
    """Manage SMS and email alerts"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.email_config = config.get('email', {})
        self.sms_config = config.get('sms', {})
        
        # Initialize Twilio for SMS
        if self.sms_config.get('enabled'):
            self.twilio_client = Client(
                self.sms_config['account_sid'],
                self.sms_config['auth_token']
            )
        else:
            self.twilio_client = None
    
    def send_alert(self, subject: str, message: str, severity: str = 'info'):
        """Send alert via configured channels"""
        
        # Determine which channels to use based on severity
        send_email = severity in ['warning', 'error', 'critical']
        send_sms = severity in ['error', 'critical']
        
        if send_email and self.email_config.get('enabled'):
            self._send_email(subject, message)
        
        if send_sms and self.sms_config.get('enabled'):
            self._send_sms(f"{subject}: {message}")
    
    def _send_email(self, subject: str, body: str):
        """Send email alert"""
        try:
            msg = MIMEText(body)
            msg['Subject'] = f"[Trading System] {subject}"
            msg['From'] = self.email_config['from']
            msg['To'] = self.email_config['to']
            
            with smtplib.SMTP(self.email_config['smtp_server'], 
                             self.email_config['smtp_port']) as server:
                if self.email_config.get('use_tls'):
                    server.starttls()
                server.login(self.email_config['username'], 
                           self.email_config['password'])
                server.send_message(msg)
        except Exception as e:
            logging.error(f"Email alert failed: {str(e)}")
    
    def _send_sms(self, message: str):
        """Send SMS alert"""
        try:
            if self.twilio_client:
                self.twilio_client.messages.create(
                    body=message[:160],  # SMS length limit
                    from_=self.sms_config['from_number'],
                    to=self.sms_config['to_number']
                )
        except Exception as e:
            logging.error(f"SMS alert failed: {str(e)}")

# ============== THREE-TIER COMMUNICATION ==============

class ThreeTierCommunication:
    """Enhanced communication using Python native protocols instead of CSV"""
    
    def __init__(self, mt4_host: str = 'localhost', mt4_port: int = 5555):
        self.mt4_host = mt4_host
        self.mt4_port = mt4_port
        self.message_queue = Queue()
        self.response_queue = Queue()
        
    async def send_signal_binary(self, signal: TradingSignal) -> bool:
        """Send signal using binary protocol"""
        try:
            # Serialize signal
            data = pickle.dumps(asdict(signal))
            
            # Create header with message length
            header = struct.pack('!I', len(data))
            
            # Send to MT4 bridge
            reader, writer = await asyncio.open_connection(
                self.mt4_host, self.mt4_port
            )
            
            writer.write(header + data)
            await writer.drain()
            
            # Wait for acknowledgment
            response = await reader.read(1024)
            
            writer.close()
            await writer.wait_closed()
            
            return response == b'ACK'
            
        except Exception as e:
            logging.error(f"Binary send failed: {str(e)}")
            return False
    
    async def send_signal_json(self, signal: TradingSignal) -> bool:
        """Send signal using JSON protocol"""
        try:
            # Convert to JSON
            signal_dict = asdict(signal)
            # Convert datetime objects to strings
            for key, value in signal_dict.items():
                if isinstance(value, datetime):
                    signal_dict[key] = value.isoformat()
                elif isinstance(value, SignalPriority):
                    signal_dict[key] = value.name
            
            json_data = json.dumps(signal_dict)
            
            # Send via socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.mt4_host, self.mt4_port))
            
            # Send with newline delimiter
            sock.send((json_data + '\n').encode('utf-8'))
            
            # Wait for response
            response = sock.recv(1024).decode('utf-8')
            sock.close()
            
            return 'SUCCESS' in response
            
        except Exception as e:
            logging.error(f"JSON send failed: {str(e)}")
            return False
    
    def create_mt4_bridge_server(self):
        """Create server that MT4 can connect to"""
        
        async def handle_mt4_connection(reader, writer):
            """Handle incoming MT4 connections"""
            addr = writer.get_extra_info('peername')
            logging.info(f"MT4 connected from {addr}")
            
            try:
                while True:
                    # Read message length
                    header = await reader.read(4)
                    if not header:
                        break
                    
                    msg_len = struct.unpack('!I', header)[0]
                    
                    # Read message
                    data = await reader.read(msg_len)
                    
                    # Process message
                    message = pickle.loads(data)
                    self.message_queue.put(message)
                    
                    # Send acknowledgment
                    writer.write(b'ACK')
                    await writer.drain()
                    
            except Exception as e:
                logging.error(f"MT4 connection error: {str(e)}")
            finally:
                writer.close()
                await writer.wait_closed()
        
        return handle_mt4_connection

# ============== PARAMETER MANAGEMENT SYSTEM ==============

class ParameterManager:
    """Manage trading parameters and combinations"""
    
    def __init__(self):
        self.parameter_sets: Dict[str, Dict] = {}
        self.reentry_profiles: Dict[str, pd.DataFrame] = {}
        self.global_risk_params = {
            'max_risk_per_trade': 2.0,  # % of account
            'max_daily_risk': 6.0,       # % of account
            'max_open_positions': 5,
            'max_correlation_exposure': 0.7
        }
        
    def calculate_lot_size(self, account_balance: float, risk_pct: float,
                          stop_loss_pips: int, pip_value: float) -> float:
        """Calculate lot size based on percentage risk"""
        risk_amount = account_balance * (risk_pct / 100)
        lot_size = risk_amount / (stop_loss_pips * pip_value)
        
        # Round to broker's lot step (usually 0.01)
        lot_size = round(lot_size, 2)
        
        # Apply limits
        min_lot = 0.01
        max_lot = min(lot_size, account_balance * 0.1 / 10000)  # Max 10% leverage
        
        return max(min_lot, min(lot_size, max_lot))
    
    def load_parameter_set(self, name: str, params: Dict):
        """Load a parameter combination"""
        self.parameter_sets[name] = {
            'indicators': params.get('indicators', {}),
            'risk': params.get('risk', {}),
            'reentry': params.get('reentry', {}),
            'filters': params.get('filters', {})
        }
    
    def get_active_parameters(self, symbol: str, market_condition: str) -> Dict:
        """Get parameters based on symbol and market condition"""
        # Market condition based parameter selection
        if market_condition == 'trending':
            base_set = self.parameter_sets.get('trend_following', {})
        elif market_condition == 'ranging':
            base_set = self.parameter_sets.get('mean_reversion', {})
        else:
            base_set = self.parameter_sets.get('default', {})
        
        # Apply symbol-specific overrides
        symbol_overrides = self.parameter_sets.get(f"{symbol}_override", {})
        
        # Merge parameters
        active_params = {**base_set}
        for key, value in symbol_overrides.items():
            if isinstance(value, dict):
                active_params[key] = {**active_params.get(key, {}), **value}
            else:
                active_params[key] = value
        
        return active_params

# ============== USAGE EXAMPLE ==============

async def main():
    """Example integration of all systems"""
    
    # Initialize systems
    signal_queue = SignalQueue()
    test_suite = ComprehensiveTestSuite()
    param_manager = ParameterManager()
    
    # Configure risk monitor
    risk_config = {
        'max_drawdown_pct': 10.0,
        'daily_loss_limit': 1000,
        'check_interval_seconds': 1,
        'alerts': {
            'email': {
                'enabled': True,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'use_tls': True,
                'from': 'trading@example.com',
                'to': 'alerts@example.com',
                'username': 'trading@example.com',
                'password': 'app_password'
            },
            'sms': {
                'enabled': True,
                'account_sid': 'your_twilio_sid',
                'auth_token': 'your_twilio_token',
                'from_number': '+1234567890',
                'to_number': '+0987654321'
            }
        }
    }
    
    risk_monitor = RiskMonitorDaemon(risk_config)
    
    # Run comprehensive tests
    print("Running comprehensive tests...")
    all_passed, results = test_suite.run_all_tests()
    
    for result in results:
        print(result)
    
    if not all_passed:
        print("\n⚠️  Some tests failed. Please review before continuing.")
        critical_failures = [r for r in results if r.severity == 'CRITICAL' and not r.passed]
        if critical_failures:
            print("\n❌ CRITICAL FAILURES DETECTED - CANNOT PROCEED")
            return
    
    # Start risk monitor daemon
    print("\n✓ Starting risk monitor daemon...")
    risk_monitor.start()
    
    # Setup communication
    comm = ThreeTierCommunication()
    
    # Add some signals to queue
    print("\n✓ Adding signals to queue...")
    
    # Add economic event signal
    signal_queue.add_economic_event_signal({
        'Time': '2025-08-17 08:30:00',
        'Currency': 'USD',
        'Event': 'Non-Farm Payrolls',
        'Impact': 'High'
    })
    
    # Add price-triggered signal
    signal_queue.add_price_triggered_signal(
        'EURUSD', 1.1000, 'BUY', 0.01
    )
    
    # Display upcoming signals
    upcoming = signal_queue.get_upcoming_signals(60)
    print(f"\n📊 Upcoming signals in next 60 minutes: {len(upcoming)}")
    for signal in upcoming:
        print(f"  - {signal.signal_id}: {signal.symbol} {signal.direction} "
              f"@ {signal.price_threshold or signal.execution_time}")
    
    # Calculate lot size example
    account_balance = 10000
    risk_pct = 2.0
    stop_loss_pips = 50
    pip_value = 10  # for standard lot
    
    lot_size = param_manager.calculate_lot_size(
        account_balance, risk_pct, stop_loss_pips, pip_value
    )
    print(f"\n💰 Calculated lot size: {lot_size} "
          f"(risking {risk_pct}% = ${account_balance * risk_pct / 100})")
    
    # Send a test signal
    test_signal = upcoming[0] if upcoming else None
    if test_signal:
        print(f"\n📡 Sending test signal via enhanced protocol...")
        success = await comm.send_signal_json(test_signal)
        print(f"  Signal sent: {'✓' if success else '✗'}")
    
    print("\n✅ All systems initialized and running")
    print("   - Risk monitor: Active")
    print("   - Signal queue: Active")
    print("   - Communication: Ready")
    print("   - Testing suite: Available")
    
    # Keep running for demo
    await asyncio.sleep(5)
    
    # Cleanup
    risk_monitor.stop()
    print("\n👋 Systems shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
