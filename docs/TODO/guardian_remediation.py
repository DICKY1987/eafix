#!/usr/bin/env python3
"""
Guardian Remediation Engine - Trading-Specific Recovery Actions
Implements idempotent, broker-reconciled recovery procedures
"""

import asyncio
import json
import logging
import sqlite3
import time
import uuid
import shutil
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import win32api
import win32con
import win32process


class TradingRemediationEngine:
    """Trading-specific automated recovery procedures"""
    
    def __init__(self, config: Dict, bridge_manager, ea_connector, db_manager):
        self.config = config
        self.bridge_manager = bridge_manager
        self.ea_connector = ea_connector  
        self.db_manager = db_manager
        self.recovery_history = []
        self.manual_latch_engaged = False
        self.emergency_mode = False
        
        # Recovery success tracking
        self.success_rates = {}
        self.last_recovery_times = {}
        
    async def pause_new_commands(self) -> bool:
        """Gracefully pause new trading commands at sequence boundary"""
        try:
            logging.info("Pausing new commands at sequence boundary")
            
            # Set global pause flag
            await self.bridge_manager.set_command_pause(True)
            
            # Wait for current commands to complete
            timeout = 30
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                pending_commands = await self.bridge_manager.get_pending_commands()
                if len(pending_commands) == 0:
                    break
                await asyncio.sleep(1)
            
            # Verify no new commands are being processed
            if await self.bridge_manager.is_command_processing_paused():
                logging.info("Command processing successfully paused")
                return True
            else:
                logging.error("Failed to pause command processing")
                return False
                
        except Exception as e:
            logging.error(f"Failed to pause new commands: {e}")
            return False
    
    async def reset_bridges(self) -> bool:
        """Reset all communication channels in proper order"""
        try:
            logging.info("Resetting all communication bridges")
            
            # 1. Quiesce active commands
            await self.bridge_manager.quiesce_at_sequence_boundary()
            
            # 2. Close all connections gracefully
            await self.bridge_manager.close_socket_bridge()
            await self.bridge_manager.close_csv_bridge()
            await self.bridge_manager.close_named_pipe_bridge()
            
            # 3. Clear internal state
            await self.bridge_manager.clear_connection_cache()
            
            # 4. Re-initialize in priority order
            bridges_initialized = 0
            
            # Try socket first
            if await self.bridge_manager.initialize_socket_bridge():
                bridges_initialized += 1
                logging.info("Socket bridge reinitialized")
            
            # CSV as fallback
            if await self.bridge_manager.initialize_csv_bridge():
                bridges_initialized += 1
                logging.info("CSV bridge reinitialized")
            
            # Named pipes as last resort
            if await self.bridge_manager.initialize_named_pipe_bridge():
                bridges_initialized += 1
                logging.info("Named pipe bridge reinitialized")
            
            if bridges_initialized > 0:
                # Resume command processing
                await self.bridge_manager.set_command_pause(False)
                logging.info(f"Bridge reset complete: {bridges_initialized} bridges active")
                return True
            else:
                logging.error("Failed to initialize any communication bridge")
                await self._engage_emergency_mode()
                return False
                
        except Exception as e:
            logging.error(f"Bridge reset failed: {e}")
            return False
    
    async def restart_ea(self) -> bool:
        """Restart EA via DDE or process manipulation"""
        try:
            logging.info("Attempting EA restart")
            
            # 1. Try graceful restart via DDE first
            restart_success = await self._restart_ea_via_dde()
            
            if not restart_success:
                # 2. Try process-level restart
                restart_success = await self._restart_ea_via_process()
            
            if restart_success:
                # 3. Verify EA is responsive
                for attempt in range(5):
                    await asyncio.sleep(10)  # Wait for EA initialization
                    if await self._verify_ea_responsive():
                        logging.info("EA restart successful and verified")
                        return True
                    logging.info(f"EA restart verification attempt {attempt + 1}/5")
                
                logging.error("EA restarted but not responsive")
                return False
            else:
                logging.error("Failed to restart EA")
                return False
                
        except Exception as e:
            logging.error(f"EA restart failed: {e}")
            return False
    
    async def _restart_ea_via_dde(self) -> bool:
        """Attempt EA restart via DDE commands"""
        try:
            # Send EA restart command via DDE
            dde_commands = [
                "EA_DISABLE",
                "EA_REMOVE_FROM_CHART", 
                "EA_REATTACH_TO_CHART",
                "EA_ENABLE"
            ]
            
            for command in dde_commands:
                success = await self.ea_connector.send_dde_command(command, timeout=10)
                if not success:
                    logging.warning(f"DDE command failed: {command}")
                    return False
                await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            logging.error(f"DDE restart failed: {e}")
            return False
    
    async def _restart_ea_via_process(self) -> bool:
        """Restart EA by manipulating MT4 process"""
        try:
            # Find MT4 processes
            mt4_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                if 'terminal.exe' in proc.info['name'].lower():
                    mt4_processes.append(proc)
            
            if not mt4_processes:
                logging.error("No MT4 processes found")
                return False
            
            # For each MT4 process, try to restart EA
            for proc in mt4_processes:
                try:
                    # Send window message to restart EA
                    hwnd = win32api.FindWindow(None, f"MetaTrader 4 - {proc.pid}")
                    if hwnd:
                        # Send custom restart message
                        win32api.SendMessage(hwnd, win32con.WM_USER + 100, 0, 0)
                        await asyncio.sleep(5)
                        
                        if await self._verify_ea_responsive():
                            return True
                            
                except Exception as e:
                    logging.warning(f"Failed to restart EA on process {proc.pid}: {e}")
                    continue
            
            return False
            
        except Exception as e:
            logging.error(f"Process-level EA restart failed: {e}")
            return False
    
    async def reconcile_with_broker(self) -> bool:
        """Reconcile all positions and orders with broker state"""
        try:
            logging.info("Starting broker reconciliation")
            
            # 1. Get current state from broker
            broker_positions = await self._get_broker_positions()
            broker_orders = await self._get_broker_orders()
            
            # 2. Get local state from database
            local_positions = await self.db_manager.get_active_positions()
            local_orders = await self.db_manager.get_active_orders()
            
            # 3. Identify discrepancies
            position_discrepancies = self._find_position_discrepancies(
                broker_positions, local_positions
            )
            order_discrepancies = self._find_order_discrepancies(
                broker_orders, local_orders
            )
            
            # 4. Reconcile positions
            for discrepancy in position_discrepancies:
                await self._reconcile_position(discrepancy)
            
            # 5. Reconcile orders
            for discrepancy in order_discrepancies:
                await self._reconcile_order(discrepancy)
            
            # 6. Update local database with broker truth
            await self._update_local_state_from_broker(broker_positions, broker_orders)
            
            logging.info(f"Broker reconciliation complete: {len(position_discrepancies)} position fixes, {len(order_discrepancies)} order fixes")
            return True
            
        except Exception as e:
            logging.error(f"Broker reconciliation failed: {e}")
            return False
    
    async def switch_to_csv_bridge(self) -> bool:
        """Failover to CSV bridge communication"""
        try:
            logging.info("Switching to CSV bridge")
            
            # 1. Ensure CSV bridge is healthy
            if not await self.bridge_manager.test_csv_bridge():
                await self.bridge_manager.repair_csv_bridge()
            
            # 2. Quiesce commands at sequence boundary
            await self.bridge_manager.quiesce_at_sequence_boundary()
            
            # 3. Switch primary bridge
            await self.bridge_manager.set_primary_bridge("csv")
            
            # 4. Test new bridge with ping
            test_success = await self.bridge_manager.test_bridge_latency("csv")
            
            if test_success and test_success < 2000:  # Under 2s acceptable
                # 5. Resume command processing
                await self.bridge_manager.set_command_pause(False)
                
                # 6. Start background socket recovery
                asyncio.create_task(self._background_socket_recovery())
                
                logging.info("Successfully switched to CSV bridge")
                return True
            else:
                logging.error("CSV bridge test failed after switch")
                return False
                
        except Exception as e:
            logging.error(f"CSV bridge switch failed: {e}")
            return False
    
    async def close_positions_graceful(self, max_slippage_pips: int = 5) -> bool:
        """Gracefully close all open positions with slippage limits"""
        try:
            logging.info("Closing all positions gracefully")
            
            # 1. Get all open positions
            open_positions = await self._get_broker_positions()
            open_positions = [pos for pos in open_positions if pos['status'] == 'open']
            
            if not open_positions:
                logging.info("No open positions to close")
                return True
            
            # 2. Group positions by symbol for efficient closing
            positions_by_symbol = {}
            for pos in open_positions:
                symbol = pos['symbol']
                if symbol not in positions_by_symbol:
                    positions_by_symbol[symbol] = []
                positions_by_symbol[symbol].append(pos)
            
            # 3. Close positions by symbol
            close_results = []
            for symbol, positions in positions_by_symbol.items():
                for position in positions:
                    try:
                        close_result = await self._close_single_position(
                            position, max_slippage_pips
                        )
                        close_results.append(close_result)
                        
                        # Brief delay to avoid overwhelming broker
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        logging.error(f"Failed to close position {position['ticket']}: {e}")
                        close_results.append(False)
            
            # 4. Verify all positions are closed
            success_count = sum(1 for result in close_results if result)
            total_positions = len(open_positions)
            
            if success_count == total_positions:
                logging.info(f"All {total_positions} positions closed successfully")
                return True
            else:
                logging.warning(f"Only {success_count}/{total_positions} positions closed")
                
                # Force close remaining positions if graceful close failed
                remaining_positions = await self._get_broker_positions()
                remaining_open = [pos for pos in remaining_positions if pos['status'] == 'open']
                
                if remaining_open:
                    logging.info("Force closing remaining positions")
                    for position in remaining_open:
                        await self._force_close_position(position)
                
                return success_count > total_positions * 0.8  # 80% success threshold
                
        except Exception as e:
            logging.error(f"Graceful position closure failed: {e}")
            return False
    
    async def engage_manual_latch(self, conditions: List[str]) -> bool:
        """Engage manual latch requiring human intervention to reset"""
        try:
            logging.critical("Engaging manual latch - human intervention required")
            
            # 1. Set manual latch flag
            self.manual_latch_engaged = True
            
            # 2. Disable all automated trading
            await self.bridge_manager.disable_automated_trading()
            
            # 3. Create latch record in database
            latch_record = {
                'timestamp': datetime.utcnow(),
                'conditions': conditions,
                'trigger_reason': 'automated_remediation_failure',
                'status': 'engaged'
            }
            
            await self.db_manager.create_manual_latch_record(latch_record)
            
            # 4. Send critical notifications
            await self._send_critical_alert([
                'sms', 'email', 'desktop', 'teams'
            ], "MANUAL LATCH ENGAGED - Trading system requires human intervention")
            
            logging.critical("Manual latch successfully engaged")
            return True
            
        except Exception as e:
            logging.error(f"Failed to engage manual latch: {e}")
            return False
    
    async def create_emergency_checkpoint(self) -> bool:
        """Create emergency state checkpoint for recovery"""
        try:
            logging.info("Creating emergency state checkpoint")
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            checkpoint_dir = Path(f"emergency_checkpoints/checkpoint_{timestamp}")
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
            # 1. Backup database
            db_backup_path = checkpoint_dir / "huey_emergency.db"
            shutil.copy2(self.db_manager.db_path, db_backup_path)
            
            # 2. Backup configuration files
            config_backup_dir = checkpoint_dir / "config"
            config_backup_dir.mkdir(exist_ok=True)
            for config_file in Path("config").glob("*.yaml"):
                shutil.copy2(config_file, config_backup_dir)
            
            # 3. Export current system state
            system_state = {
                'timestamp': datetime.utcnow().isoformat(),
                'active_positions': await self._get_broker_positions(),
                'pending_orders': await self._get_broker_orders(),
                'system_metrics': await self._gather_system_metrics(),
                'bridge_status': await self.bridge_manager.get_bridge_status(),
                'recent_commands': await self.bridge_manager.get_recent_commands(100)
            }
            
            state_file = checkpoint_dir / "system_state.json"
            with open(state_file, 'w') as f:
                json.dump(system_state, f, indent=2, default=str)
            
            # 4. Create integrity hash
            import hashlib
            checkpoint_hash = hashlib.sha256()
            for file_path in checkpoint_dir.rglob('*'):
                if file_path.is_file():
                    with open(file_path, 'rb') as f:
                        checkpoint_hash.update(f.read())
            
            hash_file = checkpoint_dir / "checkpoint.sha256"
            with open(hash_file, 'w') as f:
                f.write(checkpoint_hash.hexdigest())
            
            logging.info(f"Emergency checkpoint created: {checkpoint_dir}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create emergency checkpoint: {e}")
            return False
    
    async def _background_socket_recovery(self):
        """Background task to recover socket bridge"""
        max_attempts = 10
        base_delay = 30  # Start with 30 seconds
        
        for attempt in range(max_attempts):
            try:
                # Exponential backoff with jitter
                delay = min(base_delay * (2 ** attempt), 300)  # Max 5 minutes
                jitter = delay * 0.1 * (0.5 - random.random())  # ±10% jitter
                await asyncio.sleep(delay + jitter)
                
                logging.info(f"Socket recovery attempt {attempt + 1}/{max_attempts}")
                
                # Attempt socket bridge recovery
                if await self.bridge_manager.test_socket_bridge_recovery():
                    # Switch back to socket if it's working well
                    socket_latency = await self.bridge_manager.test_bridge_latency("socket")
                    csv_latency = await self.bridge_manager.test_bridge_latency("csv")
                    
                    if socket_latency and socket_latency < csv_latency * 0.8:
                        # Socket is significantly better, switch back
                        await self.bridge_manager.quiesce_at_sequence_boundary()
                        await self.bridge_manager.set_primary_bridge("socket")
                        await self.bridge_manager.set_command_pause(False)
                        
                        logging.info("Successfully recovered and switched back to socket bridge")
                        return
                
            except Exception as e:
                logging.warning(f"Socket recovery attempt {attempt + 1} failed: {e}")
        
        logging.warning("Socket bridge recovery failed after all attempts")
    
    async def _verify_ea_responsive(self) -> bool:
        """Verify EA is responsive to commands"""
        try:
            # Send test heartbeat
            start_time = time.time()
            response = await self.ea_connector.send_heartbeat(timeout=5)
            response_time = time.time() - start_time
            
            return response and response_time < 3.0
            
        except Exception as e:
            logging.warning(f"EA responsiveness check failed: {e}")
            return False
    
    async def _close_single_position(self, position: Dict, max_slippage_pips: int) -> bool:
        """Close a single position with slippage control"""
        try:
            close_command = {
                'op': 'CLOSE_POSITION',
                'ticket': position['ticket'],
                'symbol': position['symbol'],
                'lots': position['lots'],
                'max_slippage_pips': max_slippage_pips,
                'timeout_seconds': 30
            }
            
            response = await self.ea_connector.send_trade_command(close_command)
            
            if response and response.get('status') == 'success':
                logging.info(f"Position {position['ticket']} closed successfully")
                return True
            else:
                logging.warning(f"Failed to close position {position['ticket']}: {response}")
                return False
                
        except Exception as e:
            logging.error(f"Error closing position {position['ticket']}: {e}")
            return False
    
    async def _send_critical_alert(self, channels: List[str], message: str) -> bool:
        """Send critical alert via multiple channels"""
        try:
            alert_record = {
                'timestamp': datetime.utcnow(),
                'level': 'CRITICAL',
                'message': message,
                'channels': channels,
                'system_state': await self._gather_system_metrics()
            }
            
            success_count = 0
            
            for channel in channels:
                try:
                    if channel == 'email':
                        success = await self._send_email_alert(message, alert_record)
                    elif channel == 'sms':
                        success = await self._send_sms_alert(message)
                    elif channel == 'desktop':
                        success = await self._send_desktop_notification(message)
                    elif channel == 'teams':
                        success = await self._send_teams_alert(message, alert_record)
                    else:
                        logging.warning(f"Unknown alert channel: {channel}")
                        continue
                    
                    if success:
                        success_count += 1
                        
                except Exception as e:
                    logging.error(f"Failed to send alert via {channel}: {e}")
            
            # Record alert in database
            await self.db_manager.record_alert(alert_record)
            
            return success_count > 0
            
        except Exception as e:
            logging.error(f"Critical alert failed: {e}")
            return False
    
    async def _engage_emergency_mode(self):
        """Engage full emergency mode"""
        logging.critical("ENGAGING EMERGENCY MODE")
        
        self.emergency_mode = True
        
        # Disable all trading
        await self.bridge_manager.disable_automated_trading()
        
        # Create emergency checkpoint
        await self.create_emergency_checkpoint()
        
        # Close all positions if risk is too high
        risk_metrics = await self._check_risk_exposure()
        if risk_metrics and risk_metrics.get('account_drawdown', 0) > 15:
            await self.close_positions_graceful()
        
        # Send emergency notifications
        await self._send_critical_alert(
            ['sms', 'email', 'desktop', 'teams'],
            "EMERGENCY MODE ENGAGED - All trading systems halted"
        )
    
    # Additional helper methods...
    async def _get_broker_positions(self) -> List[Dict]:
        """Get current positions from broker"""
        # Implementation depends on broker API
        pass
    
    async def _gather_system_metrics(self) -> Dict:
        """Gather current system performance metrics"""
        return {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'process_count': len(psutil.pids()),
            'timestamp': datetime.utcnow().isoformat()
        }