#!/usr/bin/env python3
"""
Transport Layer Integrations - Multi-path communication for Guardian system
Implements socket, named pipe, and CSV spool transports with failover
"""

import asyncio
import json
import socket
import time
import uuid
import hashlib
import sqlite3
import csv
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Protocol
import win32pipe
import win32file
import win32api
import pywintypes
import logging


@dataclass
class TransportMessage:
    """Standardized message format across all transports"""
    msg_id: str
    timestamp: str
    msg_type: str  # TRADE, HEARTBEAT, STATUS, etc.
    payload: Dict[str, Any]
    checksum: str
    priority: int = 5
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate SHA256 checksum of payload"""
        payload_str = json.dumps(self.payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode()).hexdigest()
    
    def validate_checksum(self) -> bool:
        """Verify message integrity"""
        return self.checksum == self._calculate_checksum()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransportMessage':
        return cls(**data)


class Transport(Protocol):
    """Transport interface for all communication channels"""
    name: str
    
    async def send(self, message: TransportMessage) -> bool:
        """Send message, returns True if successful"""
        ...
    
    async def receive(self) -> Optional[TransportMessage]:
        """Receive message, returns None if no message available"""
        ...
    
    async def health_check(self) -> Dict[str, Any]:
        """Return health status and metrics"""
        ...
    
    async def close(self) -> None:
        """Cleanup and close transport"""
        ...


class SocketTransport:
    """High-performance TCP socket transport (primary)"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8900, 
                 timeout: float = 5.0, buffer_size: int = 8192):
        self.name = "socket"
        self.host = host
        self.port = port
        self.timeout = timeout
        self.buffer_size = buffer_size
        self.socket = None
        self.connected = False
        
        # Metrics
        self.messages_sent = 0
        self.messages_received = 0
        self.last_error = None
        self.connection_start = None
        self.latency_samples = []
        
    async def connect(self) -> bool:
        """Establish socket connection"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            
            # Enable keep-alive for reliability
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.connect, (self.host, self.port)
            )
            
            self.connected = True
            self.connection_start = time.time()
            self.last_error = None
            
            logging.info(f"Socket transport connected to {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            self.connected = False
            logging.error(f"Socket connection failed: {e}")
            return False
    
    async def send(self, message: TransportMessage) -> bool:
        """Send message over socket with timing"""
        if not self.connected:
            if not await self.connect():
                return False
        
        try:
            start_time = time.time()
            
            # Serialize message
            data = json.dumps(message.to_dict()).encode('utf-8')
            length_header = len(data).to_bytes(4, byteorder='big')
            
            # Send length + data
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.sendall, length_header + data
            )
            
            # Wait for ACK
            ack_data = await asyncio.get_event_loop().run_in_executor(
                None, self.socket.recv, 4
            )
            
            if len(ack_data) == 4 and int.from_bytes(ack_data, 'big') == 1:
                latency = (time.time() - start_time) * 1000  # ms
                self._record_latency(latency)
                self.messages_sent += 1
                return True
            else:
                self.last_error = "Invalid ACK received"
                return False
                
        except Exception as e:
            self.last_error = str(e)
            self.connected = False
            logging.error(f"Socket send failed: {e}")
            return False
    
    async def receive(self) -> Optional[TransportMessage]:
        """Receive message from socket"""
        if not self.connected:
            return None
        
        try:
            # Read message length
            length_data = await asyncio.get_event_loop().run_in_executor(
                None, self.socket.recv, 4
            )
            
            if len(length_data) != 4:
                return None
            
            message_length = int.from_bytes(length_data, 'big')
            
            # Read message data
            data = b''
            while len(data) < message_length:
                chunk = await asyncio.get_event_loop().run_in_executor(
                    None, self.socket.recv, min(self.buffer_size, message_length - len(data))
                )
                if not chunk:
                    return None
                data += chunk
            
            # Send ACK
            ack = (1).to_bytes(4, byteorder='big')
            await asyncio.get_event_loop().run_in_executor(
                None, self.socket.sendall, ack
            )
            
            # Deserialize message
            message_dict = json.loads(data.decode('utf-8'))
            message = TransportMessage.from_dict(message_dict)
            
            if message.validate_checksum():
                self.messages_received += 1
                return message
            else:
                self.last_error = "Checksum validation failed"
                return None
                
        except Exception as e:
            self.last_error = str(e)
            self.connected = False
            logging.error(f"Socket receive failed: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Return socket transport health metrics"""
        return {
            "name": self.name,
            "connected": self.connected,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "avg_latency_ms": sum(self.latency_samples[-100:]) / len(self.latency_samples[-100:]) if self.latency_samples else 0,
            "last_error": self.last_error,
            "uptime_seconds": time.time() - self.connection_start if self.connection_start else 0
        }
    
    def _record_latency(self, latency_ms: float):
        """Record latency sample for metrics"""
        self.latency_samples.append(latency_ms)
        if len(self.latency_samples) > 1000:  # Keep last 1000 samples
            self.latency_samples.pop(0)
    
    async def close(self):
        """Close socket connection"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            finally:
                self.socket = None
                self.connected = False


class NamedPipeTransport:
    """Windows named pipe transport (secondary)"""
    
    def __init__(self, pipe_name: str = r"\\.\pipe\guardian_trading",
                 timeout: int = 5000, buffer_size: int = 4096):
        self.name = "named_pipe"
        self.pipe_name = pipe_name
        self.timeout = timeout
        self.buffer_size = buffer_size
        self.pipe_handle = None
        self.connected = False
        
        # Metrics
        self.messages_sent = 0
        self.messages_received = 0
        self.last_error = None
        
    async def connect(self) -> bool:
        """Connect to named pipe"""
        try:
            self.pipe_handle = win32file.CreateFile(
                self.pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            
            self.connected = True
            self.last_error = None
            logging.info(f"Named pipe transport connected to {self.pipe_name}")
            return True
            
        except pywintypes.error as e:
            self.last_error = f"Win32 error: {e}"
            self.connected = False
            logging.error(f"Named pipe connection failed: {e}")
            return False
    
    async def send(self, message: TransportMessage) -> bool:
        """Send message via named pipe"""
        if not self.connected:
            if not await self.connect():
                return False
        
        try:
            data = json.dumps(message.to_dict()).encode('utf-8')
            
            # Write message
            result, bytes_written = win32file.WriteFile(self.pipe_handle, data)
            
            if result == 0 and bytes_written == len(data):
                self.messages_sent += 1
                return True
            else:
                self.last_error = f"Write failed: result={result}, bytes={bytes_written}"
                return False
                
        except pywintypes.error as e:
            self.last_error = f"Win32 error: {e}"
            self.connected = False
            logging.error(f"Named pipe send failed: {e}")
            return False
    
    async def receive(self) -> Optional[TransportMessage]:
        """Receive message from named pipe"""
        if not self.connected:
            return None
        
        try:
            # Read with timeout
            result, data = win32file.ReadFile(self.pipe_handle, self.buffer_size)
            
            if result == 0:
                message_dict = json.loads(data.decode('utf-8'))
                message = TransportMessage.from_dict(message_dict)
                
                if message.validate_checksum():
                    self.messages_received += 1
                    return message
                else:
                    self.last_error = "Checksum validation failed"
                    return None
            else:
                return None
                
        except pywintypes.error as e:
            self.last_error = f"Win32 error: {e}"
            self.connected = False
            logging.error(f"Named pipe receive failed: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Return named pipe health metrics"""
        return {
            "name": self.name,
            "connected": self.connected,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "last_error": self.last_error
        }
    
    async def close(self):
        """Close named pipe"""
        if self.pipe_handle:
            try:
                win32file.CloseHandle(self.pipe_handle)
            except:
                pass
            finally:
                self.pipe_handle = None
                self.connected = False


class CsvSpoolTransport:
    """CSV file-based transport (fallback)"""
    
    def __init__(self, spool_dir: str = "spool", 
                 poll_interval: float = 0.5,
                 max_file_age: int = 300):  # 5 minutes
        self.name = "csv_spool"
        self.spool_dir = Path(spool_dir)
        self.poll_interval = poll_interval
        self.max_file_age = max_file_age
        
        # Create spool directories
        (self.spool_dir / "outbound").mkdir(parents=True, exist_ok=True)
        (self.spool_dir / "inbound").mkdir(parents=True, exist_ok=True)
        (self.spool_dir / "processed").mkdir(parents=True, exist_ok=True)
        
        # Metrics
        self.messages_sent = 0
        self.messages_received = 0
        self.last_error = None
        self.file_lock = threading.Lock()
        
    async def send(self, message: TransportMessage) -> bool:
        """Write message to CSV file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"msg_{timestamp}_{message.msg_id[:8]}.csv"
            filepath = self.spool_dir / "outbound" / filename
            
            with self.file_lock:
                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Header
                    writer.writerow(['msg_id', 'timestamp', 'msg_type', 'payload', 'checksum', 'priority'])
                    
                    # Data
                    writer.writerow([
                        message.msg_id,
                        message.timestamp,
                        message.msg_type,
                        json.dumps(message.payload),
                        message.checksum,
                        message.priority
                    ])
            
            self.messages_sent += 1
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logging.error(f"CSV spool send failed: {e}")
            return False
    
    async def receive(self) -> Optional[TransportMessage]:
        """Read message from CSV file"""
        try:
            inbound_dir = self.spool_dir / "inbound"
            csv_files = list(inbound_dir.glob("*.csv"))
            
            if not csv_files:
                return None
            
            # Process oldest file first
            oldest_file = min(csv_files, key=lambda f: f.stat().st_mtime)
            
            with self.file_lock:
                try:
                    with open(oldest_file, 'r', newline='', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        row = next(reader)
                        
                        message = TransportMessage(
                            msg_id=row['msg_id'],
                            timestamp=row['timestamp'],
                            msg_type=row['msg_type'],
                            payload=json.loads(row['payload']),
                            checksum=row['checksum'],
                            priority=int(row['priority'])
                        )
                        
                        if message.validate_checksum():
                            # Move processed file
                            processed_path = self.spool_dir / "processed" / oldest_file.name
                            oldest_file.rename(processed_path)
                            
                            self.messages_received += 1
                            return message
                        else:
                            self.last_error = "Checksum validation failed"
                            oldest_file.unlink()  # Delete corrupted file
                            return None
                            
                except Exception as e:
                    self.last_error = f"Error processing {oldest_file.name}: {e}"
                    oldest_file.unlink()  # Delete problematic file
                    return None
                    
        except Exception as e:
            self.last_error = str(e)
            logging.error(f"CSV spool receive failed: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Return CSV spool health metrics"""
        try:
            outbound_count = len(list((self.spool_dir / "outbound").glob("*.csv")))
            inbound_count = len(list((self.spool_dir / "inbound").glob("*.csv")))
            processed_count = len(list((self.spool_dir / "processed").glob("*.csv")))
            
            # Check for old files
            old_files = 0
            cutoff_time = time.time() - self.max_file_age
            for filepath in (self.spool_dir / "outbound").glob("*.csv"):
                if filepath.stat().st_mtime < cutoff_time:
                    old_files += 1
            
            return {
                "name": self.name,
                "connected": True,  # File system always "connected"
                "messages_sent": self.messages_sent,
                "messages_received": self.messages_received,
                "outbound_queue": outbound_count,
                "inbound_queue": inbound_count,
                "processed_count": processed_count,
                "old_files": old_files,
                "last_error": self.last_error
            }
            
        except Exception as e:
            return {
                "name": self.name,
                "connected": False,
                "last_error": str(e)
            }
    
    async def cleanup_old_files(self):
        """Clean up old processed files"""
        try:
            cutoff_time = time.time() - (self.max_file_age * 2)
            processed_dir = self.spool_dir / "processed"
            
            for filepath in processed_dir.glob("*.csv"):
                if filepath.stat().st_mtime < cutoff_time:
                    filepath.unlink()
                    
        except Exception as e:
            logging.error(f"CSV cleanup failed: {e}")
    
    async def close(self):
        """Clean up CSV transport"""
        await self.cleanup_old_files()


class TransportRouter:
    """Multi-transport router with failover and store-and-forward"""
    
    def __init__(self, db_path: str = "transport_buffer.db"):
        self.transports = {}
        self.primary_transport = None
        self.db_path = db_path
        self.buffer_db = None
        self._init_buffer_db()
        
        # Metrics
        self.total_messages = 0
        self.successful_sends = 0
        self.failed_sends = 0
        self.failovers = 0
        
    def _init_buffer_db(self):
        """Initialize SQLite buffer for store-and-forward"""
        self.buffer_db = sqlite3.connect(self.db_path, check_same_thread=False)
        self.buffer_db.execute("""
            CREATE TABLE IF NOT EXISTS message_buffer (
                msg_id TEXT PRIMARY KEY,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                priority INTEGER NOT NULL DEFAULT 5,
                transport_tried TEXT,
                payload TEXT NOT NULL,
                checksum TEXT NOT NULL,
                ack_received INTEGER DEFAULT 0,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                deadline_ts DATETIME
            )
        """)
        self.buffer_db.commit()
    
    def add_transport(self, transport: Transport, is_primary: bool = False):
        """Add transport to router"""
        self.transports[transport.name] = transport
        if is_primary or not self.primary_transport:
            self.primary_transport = transport.name
    
    async def send_with_failover(self, message: TransportMessage) -> str:
        """Send message with automatic failover"""
        self.total_messages += 1
        
        # Try transports in priority order
        transport_order = [self.primary_transport] + [
            name for name in self.transports.keys() 
            if name != self.primary_transport
        ]
        
        for transport_name in transport_order:
            if transport_name not in self.transports:
                continue
                
            transport = self.transports[transport_name]
            
            try:
                # Check transport health first
                health = await transport.health_check()
                if not health.get("connected", False):
                    continue
                
                # Attempt send
                success = await transport.send(message)
                if success:
                    self.successful_sends += 1
                    
                    # Mark as acknowledged if buffered
                    await self._mark_acknowledged(message.msg_id)
                    
                    return transport_name
                
            except Exception as e:
                logging.error(f"Transport {transport_name} failed: {e}")
                continue
        
        # All transports failed - buffer the message
        self.failed_sends += 1
        await self._buffer_message(message)
        return "buffered"
    
    async def _buffer_message(self, message: TransportMessage):
        """Store message in buffer for later retry"""
        try:
            self.buffer_db.execute("""
                INSERT OR REPLACE INTO message_buffer 
                (msg_id, priority, payload, checksum, retry_count, max_retries, deadline_ts)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                message.msg_id,
                message.priority,
                json.dumps(message.to_dict()),
                message.checksum,
                message.retry_count,
                message.max_retries,
                datetime.now() + timedelta(minutes=30)  # 30 min deadline
            ))
            self.buffer_db.commit()
            
        except Exception as e:
            logging.error(f"Failed to buffer message: {e}")
    
    async def _mark_acknowledged(self, msg_id: str):
        """Mark message as successfully acknowledged"""
        try:
            self.buffer_db.execute(
                "UPDATE message_buffer SET ack_received = 1 WHERE msg_id = ?",
                (msg_id,)
            )
            self.buffer_db.commit()
        except Exception as e:
            logging.error(f"Failed to mark message acknowledged: {e}")
    
    async def replay_buffered_messages(self) -> int:
        """Replay buffered messages that haven't been acknowledged"""
        replayed = 0
        
        try:
            cursor = self.buffer_db.cursor()
            cursor.execute("""
                SELECT payload, retry_count FROM message_buffer 
                WHERE ack_received = 0 
                AND retry_count < max_retries 
                AND deadline_ts > datetime('now')
                ORDER BY priority DESC, created_at ASC
                LIMIT 100
            """)
            
            for row in cursor.fetchall():
                try:
                    payload_dict = json.loads(row[0])
                    message = TransportMessage.from_dict(payload_dict)
                    message.retry_count = row[1] + 1
                    
                    transport_used = await self.send_with_failover(message)
                    if transport_used != "buffered":
                        replayed += 1
                        
                except Exception as e:
                    logging.error(f"Failed to replay message: {e}")
                    
        except Exception as e:
            logging.error(f"Failed to replay buffered messages: {e}")
        
        return replayed
    
    async def get_transport_status(self) -> Dict[str, Any]:
        """Get status of all transports"""
        status = {}
        
        for name, transport in self.transports.items():
            try:
                health = await transport.health_check()
                status[name] = {
                    "is_primary": name == self.primary_transport,
                    **health
                }
            except Exception as e:
                status[name] = {
                    "name": name,
                    "connected": False,
                    "last_error": str(e)
                }
        
        return status
    
    async def close_all(self):
        """Close all transports and clean up"""
        for transport in self.transports.values():
            try:
                await transport.close()
            except Exception as e:
                logging.error(f"Error closing transport: {e}")
        
        if self.buffer_db:
            self.buffer_db.close()


# Example usage and integration
async def main():
    """Example usage of transport system"""
    
    # Initialize transports
    socket_transport = SocketTransport("127.0.0.1", 8900)
    pipe_transport = NamedPipeTransport(r"\\.\pipe\guardian_trading")
    csv_transport = CsvSpoolTransport("spool")
    
    # Create router with failover
    router = TransportRouter("guardian_transport.db")
    router.add_transport(socket_transport, is_primary=True)
    router.add_transport(pipe_transport)
    router.add_transport(csv_transport)
    
    # Test message
    test_message = TransportMessage(
        msg_id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        msg_type="HEARTBEAT",
        payload={"status": "alive", "timestamp": time.time()},
        checksum=""
    )
    
    # Send with automatic failover
    transport_used = await router.send_with_failover(test_message)
    print(f"Message sent via: {transport_used}")
    
    # Get transport status
    status = await router.get_transport_status()
    for name, info in status.items():
        print(f"{name}: connected={info['connected']}, primary={info.get('is_primary', False)}")
    
    # Replay any buffered messages
    replayed = await router.replay_buffered_messages()
    print(f"Replayed {replayed} buffered messages")
    
    # Cleanup
    await router.close_all()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
    print("Transport layer integrations ready for Guardian system")