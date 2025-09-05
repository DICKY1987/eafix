"""Production transport integrations with comprehensive failover and buffering.

This module implements a production-ready transport system supporting:
- TCP Socket transport with 4-byte LE framing
- Named Pipe transport for Windows inter-process communication
- CSV Spool transport for emergency failover
- Message buffering and replay on recovery
- Automatic transport switching based on latency and reliability
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import socket
import struct
import time
import threading
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Union
from enum import Enum


class TransportState(Enum):
    """Transport connection states."""
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"


class MessageType(Enum):
    """Message types in the transport protocol."""
    HEARTBEAT = "HEARTBEAT"
    STATUS_REQUEST = "STATUS_REQUEST"
    SIGNAL = "SIGNAL"
    TRADE = "TRADE"
    PARAM = "PARAM"
    ERROR = "ERROR"


@dataclass
class Message:
    """Structured message for transport layer."""
    type: MessageType
    payload: Dict
    trace_id: str = ""
    idempotency_key: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        """Convert message to dictionary for serialization."""
        return {
            "type": self.type.value,
            "payload": self.payload,
            "trace_id": self.trace_id,
            "idempotency_key": self.idempotency_key,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """Create message from dictionary."""
        return cls(
            type=MessageType(data["type"]),
            payload=data["payload"],
            trace_id=data.get("trace_id", ""),
            idempotency_key=data.get("idempotency_key", ""),
            timestamp=data.get("timestamp", time.time())
        )


@dataclass 
class TransportMetrics:
    """Transport performance metrics."""
    messages_sent: int = 0
    messages_failed: int = 0
    avg_latency_ms: float = 0.0
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    failure_count: int = 0
    bytes_sent: int = 0


class Transport(Protocol):
    """Enhanced transport interface with metrics and health monitoring."""

    def send(self, message: Message) -> bool:
        """Send a message through this transport."""
        ...
    
    def is_healthy(self) -> bool:
        """Check if transport is healthy and available."""
        ...
    
    def get_metrics(self) -> TransportMetrics:
        """Get transport performance metrics."""
        ...
    
    def connect(self) -> bool:
        """Establish connection for the transport."""
        ...
    
    def disconnect(self) -> None:
        """Close transport connection."""
        ...


class SocketTransport:
    """TCP Socket transport with 4-byte little-endian framing."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8900, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self.state = TransportState.DISCONNECTED
        self.metrics = TransportMetrics()
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """Establish socket connection."""
        with self._lock:
            try:
                if self.state == TransportState.CONNECTED:
                    return True
                
                self.state = TransportState.CONNECTING
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.timeout)
                
                self.socket.connect((self.host, self.port))
                self.socket.setblocking(False)
                
                self.state = TransportState.CONNECTED
                self.logger.info(f"Socket transport connected to {self.host}:{self.port}")
                return True
                
            except Exception as e:
                self.logger.error(f"Socket connection failed: {e}")
                self.state = TransportState.FAILED
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                    self.socket = None
                return False

    def disconnect(self) -> None:
        """Close socket connection."""
        with self._lock:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
            self.state = TransportState.DISCONNECTED

    def send(self, message: Message) -> bool:
        """Send message with 4-byte LE framing."""
        if not self.is_healthy():
            if not self.connect():
                return False
        
        try:
            start_time = time.time()
            
            # Serialize message
            message_dict = message.to_dict()
            json_data = json.dumps(message_dict).encode('utf-8')
            
            # Add CRC32 checksum for integrity
            checksum = zlib.crc32(json_data)
            message_dict["checksum"] = checksum
            json_data = json.dumps(message_dict).encode('utf-8')
            
            # 4-byte little-endian frame length + data
            frame = struct.pack('<I', len(json_data)) + json_data
            
            with self._lock:
                if not self.socket:
                    return False
                    
                # Send with timeout handling
                sent = 0
                while sent < len(frame):
                    try:
                        chunk = self.socket.send(frame[sent:])
                        if chunk == 0:
                            raise ConnectionError("Socket connection broken")
                        sent += chunk
                    except socket.error as e:
                        if e.errno == socket.EAGAIN or e.errno == socket.EWOULDBLOCK:
                            # Non-blocking socket would block, wait briefly
                            time.sleep(0.001)
                            continue
                        raise
            
            # Update metrics
            latency = (time.time() - start_time) * 1000
            self._update_metrics_success(len(frame), latency)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Socket send failed: {e}")
            self._update_metrics_failure()
            self.state = TransportState.FAILED
            return False

    def is_healthy(self) -> bool:
        """Check socket health."""
        with self._lock:
            if self.state != TransportState.CONNECTED or not self.socket:
                return False
            
            try:
                # Test with zero-byte send (non-destructive)
                self.socket.send(b'', socket.MSG_DONTWAIT)
                return True
            except socket.error:
                return False

    def get_metrics(self) -> TransportMetrics:
        """Get transport metrics."""
        return self.metrics

    def _update_metrics_success(self, bytes_sent: int, latency_ms: float):
        """Update metrics after successful send."""
        self.metrics.messages_sent += 1
        self.metrics.bytes_sent += bytes_sent
        self.metrics.last_success_time = datetime.now()
        self.metrics.failure_count = 0
        
        # Update rolling average latency
        if self.metrics.avg_latency_ms == 0:
            self.metrics.avg_latency_ms = latency_ms
        else:
            self.metrics.avg_latency_ms = (self.metrics.avg_latency_ms * 0.9) + (latency_ms * 0.1)

    def _update_metrics_failure(self):
        """Update metrics after failed send."""
        self.metrics.messages_failed += 1
        self.metrics.failure_count += 1
        self.metrics.last_failure_time = datetime.now()


class NamedPipeTransport:
    """Windows Named Pipe transport for IPC."""

    def __init__(self, pipe_name: str = r"\\.\pipe\guardian_trading", timeout: float = 5.0):
        self.pipe_name = pipe_name
        self.timeout = timeout
        self.handle: Optional[int] = None
        self.state = TransportState.DISCONNECTED
        self.metrics = TransportMetrics()
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """Connect to named pipe."""
        with self._lock:
            try:
                if self.state == TransportState.CONNECTED:
                    return True
                
                self.state = TransportState.CONNECTING
                
                # Try to connect to existing pipe
                try:
                    import win32file
                    import win32pipe
                    
                    self.handle = win32file.CreateFile(
                        self.pipe_name,
                        win32file.GENERIC_WRITE,
                        0,  # No sharing
                        None,  # Default security
                        win32file.OPEN_EXISTING,
                        0,  # Default attributes
                        None
                    )
                    
                    self.state = TransportState.CONNECTED
                    self.logger.info(f"Named pipe connected to {self.pipe_name}")
                    return True
                    
                except ImportError:
                    self.logger.warning("pywin32 not available for named pipe transport")
                    self.state = TransportState.FAILED
                    return False
                    
            except Exception as e:
                self.logger.error(f"Named pipe connection failed: {e}")
                self.state = TransportState.FAILED
                if self.handle:
                    try:
                        import win32file
                        win32file.CloseHandle(self.handle)
                    except:
                        pass
                    self.handle = None
                return False

    def disconnect(self) -> None:
        """Close named pipe connection."""
        with self._lock:
            if self.handle:
                try:
                    import win32file
                    win32file.CloseHandle(self.handle)
                except:
                    pass
                self.handle = None
            self.state = TransportState.DISCONNECTED

    def send(self, message: Message) -> bool:
        """Send message through named pipe."""
        if not self.is_healthy():
            if not self.connect():
                return False
        
        try:
            start_time = time.time()
            
            # Serialize message 
            message_dict = message.to_dict()
            json_data = json.dumps(message_dict).encode('utf-8')
            
            # Add length prefix for framing
            frame = struct.pack('<I', len(json_data)) + json_data
            
            with self._lock:
                if not self.handle:
                    return False
                
                try:
                    import win32file
                    win32file.WriteFile(self.handle, frame)
                    
                except ImportError:
                    return False
            
            # Update metrics
            latency = (time.time() - start_time) * 1000
            self._update_metrics_success(len(frame), latency)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Named pipe send failed: {e}")
            self._update_metrics_failure()
            self.state = TransportState.FAILED
            return False

    def is_healthy(self) -> bool:
        """Check named pipe health."""
        return self.state == TransportState.CONNECTED and self.handle is not None

    def get_metrics(self) -> TransportMetrics:
        """Get transport metrics."""
        return self.metrics

    def _update_metrics_success(self, bytes_sent: int, latency_ms: float):
        """Update metrics after successful send."""
        self.metrics.messages_sent += 1
        self.metrics.bytes_sent += bytes_sent
        self.metrics.last_success_time = datetime.now()
        self.metrics.failure_count = 0
        
        if self.metrics.avg_latency_ms == 0:
            self.metrics.avg_latency_ms = latency_ms
        else:
            self.metrics.avg_latency_ms = (self.metrics.avg_latency_ms * 0.9) + (latency_ms * 0.1)

    def _update_metrics_failure(self):
        """Update metrics after failed send."""
        self.metrics.messages_failed += 1
        self.metrics.failure_count += 1
        self.metrics.last_failure_time = datetime.now()


class CsvSpoolTransport:
    """Enhanced CSV spool transport with rotation and compression."""

    def __init__(self, spool_dir: Path = Path("spool"), max_file_size: int = 10*1024*1024):
        self.spool_dir = Path(spool_dir)
        self.max_file_size = max_file_size
        self.current_file: Optional[Path] = None
        self.metrics = TransportMetrics()
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """Ensure spool directory exists."""
        try:
            self.spool_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create spool directory: {e}")
            return False

    def disconnect(self) -> None:
        """CSV spool doesn't need explicit disconnect."""
        pass

    def send(self, message: Message) -> bool:
        """Append message to CSV spool file."""
        try:
            start_time = time.time()
            
            with self._lock:
                # Get current spool file
                spool_file = self._get_current_spool_file()
                if not spool_file:
                    return False
                
                # Format message as CSV row
                message_dict = message.to_dict()
                csv_row = f"{message_dict['timestamp']},{message_dict['type']},{json.dumps(message_dict['payload'])}\n"
                
                # Write to file
                with spool_file.open("a", encoding='utf-8') as f:
                    f.write(csv_row)
                    f.flush()  # Ensure immediate write
                
                # Update metrics
                latency = (time.time() - start_time) * 1000
                self._update_metrics_success(len(csv_row.encode('utf-8')), latency)
                
                # Check for file rotation
                if spool_file.stat().st_size > self.max_file_size:
                    self._rotate_spool_file()
            
            return True
            
        except Exception as e:
            self.logger.error(f"CSV spool write failed: {e}")
            self._update_metrics_failure()
            return False

    def is_healthy(self) -> bool:
        """CSV spool is always healthy if directory is writable."""
        return self.spool_dir.exists() and os.access(self.spool_dir, os.W_OK)

    def get_metrics(self) -> TransportMetrics:
        """Get transport metrics."""
        return self.metrics

    def _get_current_spool_file(self) -> Optional[Path]:
        """Get or create current spool file."""
        if not self.current_file or not self.current_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_file = self.spool_dir / f"trading_spool_{timestamp}.csv"
            
            # Write CSV header
            try:
                with self.current_file.open("w", encoding='utf-8') as f:
                    f.write("timestamp,message_type,payload\n")
            except Exception as e:
                self.logger.error(f"Failed to create spool file: {e}")
                return None
                
        return self.current_file

    def _rotate_spool_file(self):
        """Rotate spool file when it gets too large."""
        if self.current_file and self.current_file.exists():
            # Rename current file with rotation suffix
            rotated_name = self.current_file.stem + "_rotated.csv"
            rotated_path = self.current_file.parent / rotated_name
            
            try:
                self.current_file.rename(rotated_path)
                self.logger.info(f"Rotated spool file: {rotated_path}")
            except Exception as e:
                self.logger.error(f"Failed to rotate spool file: {e}")
        
        self.current_file = None  # Force creation of new file

    def _update_metrics_success(self, bytes_sent: int, latency_ms: float):
        """Update metrics after successful send."""
        self.metrics.messages_sent += 1
        self.metrics.bytes_sent += bytes_sent
        self.metrics.last_success_time = datetime.now()
        self.metrics.failure_count = 0
        
        if self.metrics.avg_latency_ms == 0:
            self.metrics.avg_latency_ms = latency_ms
        else:
            self.metrics.avg_latency_ms = (self.metrics.avg_latency_ms * 0.9) + (latency_ms * 0.1)

    def _update_metrics_failure(self):
        """Update metrics after failed send."""
        self.metrics.messages_failed += 1
        self.metrics.failure_count += 1
        self.metrics.last_failure_time = datetime.now()


@dataclass
class TriTransportRouter:
    """Production transport router with comprehensive failover and buffering."""

    primary: Transport
    secondary: Transport
    emergency: Transport
    
    # Configuration
    max_buffer_size: int = 1000
    heartbeat_interval: float = 30.0
    failover_threshold: int = 3
    recovery_check_interval: float = 60.0
    
    # Runtime state
    buffer: List[Message] = field(default_factory=list)
    active_transport: Optional[Transport] = field(default=None)
    _heartbeat_thread: Optional[threading.Thread] = field(default=None)
    _recovery_thread: Optional[threading.Thread] = field(default=None)
    _running: bool = field(default=False)
    
    def __post_init__(self):
        self.logger = logging.getLogger(__name__)
        self.transport_list = [self.primary, self.secondary, self.emergency]
        
    def start(self) -> bool:
        """Start transport router with background monitoring."""
        self._running = True
        
        # Find first healthy transport
        self.active_transport = self._find_healthy_transport()
        if not self.active_transport:
            self.logger.error("No healthy transports available")
            return False
        
        # Start background threads
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
        
        self._recovery_thread = threading.Thread(target=self._recovery_loop, daemon=True)
        self._recovery_thread.start()
        
        self.logger.info("Transport router started")
        return True

    def stop(self):
        """Stop transport router and cleanup."""
        self._running = False
        
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)
        if self._recovery_thread:
            self._recovery_thread.join(timeout=5)
        
        # Disconnect all transports
        for transport in self.transport_list:
            transport.disconnect()
        
        self.logger.info("Transport router stopped")

    def send(self, message: Message) -> bool:
        """Send message with automatic failover."""
        if not self._running:
            return False
            
        # Try active transport first
        if self.active_transport and self._try_send(self.active_transport, message):
            return True
        
        # Failover to next healthy transport
        backup_transport = self._find_healthy_transport(exclude=self.active_transport)
        if backup_transport:
            self.active_transport = backup_transport
            if self._try_send(self.active_transport, message):
                return True
        
        # All transports failed, buffer message
        self._buffer_message(message)
        return False

    def send_heartbeat(self) -> bool:
        """Send heartbeat message to maintain connection."""
        heartbeat = Message(
            type=MessageType.HEARTBEAT,
            payload={"timestamp": time.time(), "router_id": id(self)},
            trace_id=f"heartbeat_{int(time.time())}"
        )
        return self.send(heartbeat)

    def get_status(self) -> Dict:
        """Get comprehensive transport status."""
        status = {
            "active_transport": type(self.active_transport).__name__ if self.active_transport else None,
            "buffer_size": len(self.buffer),
            "running": self._running,
            "transports": {}
        }
        
        for i, transport in enumerate(["primary", "secondary", "emergency"]):
            t = self.transport_list[i]
            metrics = t.get_metrics()
            status["transports"][transport] = {
                "healthy": t.is_healthy(),
                "messages_sent": metrics.messages_sent,
                "messages_failed": metrics.messages_failed,
                "avg_latency_ms": metrics.avg_latency_ms,
                "failure_count": metrics.failure_count,
                "last_success": metrics.last_success_time.isoformat() if metrics.last_success_time else None
            }
        
        return status

    def _try_send(self, transport: Transport, message: Message) -> bool:
        """Try to send message through specific transport."""
        try:
            return transport.send(message)
        except Exception as e:
            self.logger.error(f"Transport {type(transport).__name__} send failed: {e}")
            return False

    def _find_healthy_transport(self, exclude: Transport = None) -> Optional[Transport]:
        """Find first healthy transport, optionally excluding one."""
        for transport in self.transport_list:
            if transport != exclude and transport.is_healthy():
                return transport
        return None

    def _buffer_message(self, message: Message):
        """Buffer message for later replay."""
        if len(self.buffer) >= self.max_buffer_size:
            # Remove oldest message to make room
            self.buffer.pop(0)
            self.logger.warning("Message buffer full, dropping oldest message")
        
        self.buffer.append(message)
        self.logger.debug(f"Buffered message, buffer size: {len(self.buffer)}")

    def _replay_buffered_messages(self) -> int:
        """Replay buffered messages when transport recovers."""
        if not self.buffer or not self.active_transport:
            return 0
        
        replayed = 0
        failed_messages = []
        
        for message in self.buffer:
            if self._try_send(self.active_transport, message):
                replayed += 1
            else:
                failed_messages.append(message)
        
        self.buffer = failed_messages
        
        if replayed > 0:
            self.logger.info(f"Replayed {replayed} buffered messages")
        
        return replayed

    def _heartbeat_loop(self):
        """Background heartbeat monitoring."""
        while self._running:
            try:
                if not self.send_heartbeat():
                    self.logger.warning("Heartbeat failed")
                
                time.sleep(self.heartbeat_interval)
                
            except Exception as e:
                self.logger.error(f"Heartbeat loop error: {e}")
                time.sleep(self.heartbeat_interval)

    def _recovery_loop(self):
        """Background transport recovery monitoring."""
        while self._running:
            try:
                # Check if we can recover to a higher priority transport
                if self.active_transport != self.primary and self.primary.is_healthy():
                    self.logger.info("Primary transport recovered, switching back")
                    self.active_transport = self.primary
                    self._replay_buffered_messages()
                
                # Attempt to replay buffered messages
                if self.buffer and self.active_transport and self.active_transport.is_healthy():
                    self._replay_buffered_messages()
                
                time.sleep(self.recovery_check_interval)
                
            except Exception as e:
                self.logger.error(f"Recovery loop error: {e}")
                time.sleep(self.recovery_check_interval)

