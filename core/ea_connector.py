"""
HUEY_P Trading Interface - EA Connector
Handles communication with EA through C++ bridge using HUEY_P message protocol
"""

import socket
import json
import struct
import threading
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

logger = logging.getLogger(__name__)

class EAConnector:
    """Handles communication with HUEY_P EA through C++ bridge"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 9999)
        self.timeout = config.get('timeout', 5)
        self.retry_interval = config.get('retry_interval', 10)
        
        # Connection management
        self.socket = None
        self.connected = False
        self.last_heartbeat = None
        self.connection_attempts = 0
        self.max_reconnect_attempts = 5
        
        # Message tracking
        self.pending_requests = {}
        self.message_id_counter = 0
        
        # Background thread for connection monitoring
        self.monitor_thread = None
        self.running = False
        
        # Data storage
        self.last_status_response = None
        self.last_heartbeat_data = None
        
    def connect(self) -> bool:
        """Connect to EA bridge"""
        try:
            logger.info(f"Connecting to EA bridge at {self.host}:{self.port}")
            
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            
            # Connect
            self.socket.connect((self.host, self.port))
            
            # Test connection with heartbeat
            if self.send_heartbeat():
                self.connected = True
                self.connection_attempts = 0
                logger.info("Connected to EA bridge successfully")
                
                # Start monitoring thread
                self.start_monitoring()
                return True
            else:
                logger.error("Failed to establish communication with EA bridge")
                self.disconnect()
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to EA bridge: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """Disconnect from EA bridge"""
        self.connected = False
        self.running = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        
        logger.info("Disconnected from EA bridge")
    
    def start_monitoring(self):
        """Start background monitoring thread"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_connection, daemon=True)
        self.monitor_thread.start()
    
    def monitor_connection(self):
        """Monitor connection health and attempt reconnection if needed"""
        last_heartbeat_attempt = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Send heartbeat every 30 seconds
                if current_time - last_heartbeat_attempt > 30:
                    if not self.send_heartbeat():
                        logger.warning("Heartbeat failed, connection may be lost")
                        self.connected = False
                    last_heartbeat_attempt = current_time
                
                # Attempt reconnection if disconnected
                if not self.connected and self.connection_attempts < self.max_reconnect_attempts:
                    logger.info("Attempting to reconnect to EA bridge")
                    self.connection_attempts += 1
                    
                    if self.connect():
                        logger.info("Reconnected to EA bridge successfully")
                    else:
                        time.sleep(self.retry_interval)
                
            except Exception as e:
                logger.error(f"Error in connection monitoring: {e}")
            
            time.sleep(5)  # Check every 5 seconds
    
    def generate_message_id(self) -> str:
        """Generate unique message ID"""
        self.message_id_counter += 1
        return f"py_{self.message_id_counter}_{int(time.time())}"
    
    def create_message(self, message_type: str, payload: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a message according to HUEY_P protocol"""
        message = {
            "message_type": message_type,
            "message_id": self.generate_message_id(),
            "timestamp": time.time(),
            "payload": payload,
            "source": "python",
            "version": "1.0"
        }
        
        if correlation_id:
            message["correlation_id"] = correlation_id
        
        return message
    
    def send_message(self, message: Dict[str, Any]) -> bool:
        """Send message using HUEY_P binary transport format"""
        if not self.connected or not self.socket:
            return False
        
        try:
            # Serialize message to JSON
            json_data = json.dumps(message).encode('utf-8')
            
            # Create 4-byte little-endian length header
            length = len(json_data)
            header = struct.pack('<I', length)
            
            # Send header + message
            self.socket.sendall(header + json_data)
            
            logger.debug(f"Sent message: {message['message_type']} (ID: {message['message_id']})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.connected = False
            return False
    
    def receive_message(self, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Receive message using HUEY_P binary transport format"""
        if not self.connected or not self.socket:
            return None
        
        try:
            # Set socket timeout
            self.socket.settimeout(timeout)
            
            # Read 4-byte length header
            header_data = self.socket.recv(4)
            if len(header_data) != 4:
                return None
            
            # Unpack length
            length = struct.unpack('<I', header_data)[0]
            
            # Validate length
            if length > 65536:  # Max message size 64KB
                logger.error(f"Invalid message length: {length}")
                return None
            
            # Read message data
            message_data = b''
            while len(message_data) < length:
                chunk = self.socket.recv(length - len(message_data))
                if not chunk:
                    return None
                message_data += chunk
            
            # Decode and parse JSON
            message = json.loads(message_data.decode('utf-8'))
            
            logger.debug(f"Received message: {message['message_type']} (ID: {message['message_id']})")
            return message
            
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            self.connected = False
            return None
    
    def send_heartbeat(self) -> bool:
        """Send heartbeat message"""
        payload = {
            "status": "alive",
            "timestamp": time.time(),
            "component": "python_interface"
        }
        
        message = self.create_message("HEARTBEAT", payload)
        return self.send_message(message)
    
    def request_status(self) -> Optional[Dict[str, Any]]:
        """Request status from EA"""
        payload = {
            "requested_info": ["health", "statistics", "configuration"],
            "detail_level": "DETAILED"
        }
        
        message = self.create_message("STATUS_REQUEST", payload)
        
        if self.send_message(message):
            # Wait for response
            response = self.receive_message(timeout=10.0)
            if response and response.get('message_type') == 'STATUS_RESPONSE':
                self.last_status_response = response
                return response.get('payload', {})
        
        return None
    
    def get_heartbeat(self) -> Optional[Dict[str, Any]]:
        """Get heartbeat data from EA"""
        if not self.send_heartbeat():
            return None
        
        # Wait for heartbeat response or any message
        response = self.receive_message(timeout=3.0)
        if response:
            if response.get('message_type') == 'HEARTBEAT':
                self.last_heartbeat_data = response.get('payload', {})
                self.last_heartbeat = datetime.now()
                return self.last_heartbeat_data
            elif response.get('message_type') == 'STATUS_RESPONSE':
                self.last_status_response = response
                return response.get('payload', {})
        
        return self.last_heartbeat_data
    
    def get_live_metrics(self) -> Optional[Dict[str, Any]]:
        """Get live trading metrics from EA"""
        status_data = self.request_status()
        if status_data:
            # Extract live metrics from status response
            statistics = status_data.get('statistics', {})
            health_checks = status_data.get('health_checks', {})
            
            return {
                'ea_state': health_checks.get('ea_state', 'UNKNOWN'),
                'recovery_state': health_checks.get('recovery_state', 'UNKNOWN'),
                'active_trades': statistics.get('active_trades', 0),
                'daily_profit': statistics.get('daily_profit', 0.0),
                'account_equity': statistics.get('account_equity', 0.0),
                'daily_drawdown': statistics.get('daily_drawdown', 0.0),
                'uptime_seconds': statistics.get('uptime_seconds', 0),
                'trade_count': statistics.get('trade_count', 0),
                'win_rate': statistics.get('win_rate', 0.0),
                'connection_status': health_checks.get('connection_status', 'UNKNOWN'),
                'last_trade_time': statistics.get('last_trade_time', None)
            }
        
        return None
    
    def send_signal(self, symbol: str, action: str, confidence: float, **kwargs) -> bool:
        """Send trading signal to EA"""
        payload = {
            "symbol": symbol,
            "action": action,
            "confidence": confidence,
            "strategy_id": kwargs.get('strategy_id', 'manual'),
            "signal_time": time.time()
        }
        
        # Add optional parameters
        optional_fields = ['stop_loss', 'take_profit', 'lot_size', 'magic_number', 'expiry_time']
        for field in optional_fields:
            if field in kwargs:
                payload[field] = kwargs[field]
        
        message = self.create_message("SIGNAL", payload)
        return self.send_message(message)
    
    def get_error_log(self) -> List[Dict[str, Any]]:
        """Get recent error messages"""
        # This would require the EA to maintain an error log and respond to specific requests
        # For now, return empty list as this would need to be implemented in the EA
        return []
    
    def is_connected(self) -> bool:
        """Check if connected to EA bridge"""
        return self.connected and self.socket is not None
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            'connected': self.connected,
            'host': self.host,
            'port': self.port,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'connection_attempts': self.connection_attempts,
            'max_attempts': self.max_reconnect_attempts
        }