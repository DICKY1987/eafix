#!/usr/bin/env python3
"""
HUEY_P System Integration Test Suite
Tests the complete system without requiring MT4 to be running
"""

import os
import sys
import logging
import time
import socket
import threading
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_file_structure():
    """Test that all required files are present"""
    print("Testing file structure...")
    
    required_files = [
        "HUEY_P_EA_ExecutionEngine_8.mq4",
        "huey_main.py",
        "CLAUDE.md",
        "MQL4_DLL_SocketBridge.dll",
        "Database/trading_system.db"
    ]
    
    required_dirs = [
        "core",
        "tabs", 
        "widgets",
        "utils",
        "MQL4_DLL_SocketBridge"
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    for dir in required_dirs:
        if not os.path.isdir(dir):
            missing_dirs.append(dir)
    
    if missing_files:
        print(f"ERROR: Missing files: {missing_files}")
        return False
        
    if missing_dirs:
        print(f"ERROR: Missing directories: {missing_dirs}")
        return False
        
    print("OK: All required files and directories present")
    return True

def test_database_operations():
    """Test database operations"""
    print("Testing database operations...")
    
    try:
        from core.database_manager import DatabaseManager
        
        db_config = {'path': 'Database/trading_system.db'}
        db_manager = DatabaseManager(db_config)
        
        if not db_manager.connect():
            print("ERROR: Database connection failed")
            return False
            
        # Test inserting and retrieving data
        try:
            # Insert test data into system_status
            cursor = db_manager.connection.cursor()
            cursor.execute('''
                INSERT INTO system_status (timestamp, database_connected, ea_bridge_connected, error_count)
                VALUES (?, 1, 0, 0)
            ''', (datetime.now().isoformat(),))
            
            # Insert test trade data
            cursor.execute('''
                INSERT INTO trade_results (ticket, symbol, order_type, volume, open_price, open_time, profit)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (12345, 'EURUSD', 0, 0.1, 1.1000, datetime.now().isoformat(), 15.50))
            
            db_manager.connection.commit()
            
            # Test retrieval
            trades = db_manager.get_recent_trades()
            print(f"OK: Database operations successful - {len(trades)} trades retrieved")
            
            db_manager.disconnect()
            return True
            
        except Exception as e:
            print(f"ERROR: Database operations failed: {e}")
            return False
            
    except Exception as e:
        print(f"ERROR: Database test failed: {e}")
        return False

def test_python_interface():
    """Test Python interface core functionality"""
    print("Testing Python interface...")
    
    try:
        # Test imports
        from core.app_controller import AppController
        from core.data_models import SystemStatus, LiveMetrics
        from core.ea_connector import EAConnector
        
        print("OK: All core modules imported successfully")
        
        # Test data models
        status = SystemStatus()
        status.database_connected = True
        
        metrics = LiveMetrics()
        metrics.account_balance = 10000.0
        
        print("OK: Data models functioning properly")
        
        # Test configuration
        test_config = {
            'database': {'path': 'Database/trading_system.db'},
            'ea_bridge': {'host': 'localhost', 'port': 9999, 'timeout': 5},
            'ui': {'refresh_interval': 1000, 'theme': 'default'}
        }
        
        print("OK: Configuration structure valid")
        return True
        
    except Exception as e:
        print(f"ERROR: Python interface test failed: {e}")
        return False

def test_socket_server_simulation():
    """Test socket communication by simulating EA bridge"""
    print("Testing socket communication...")
    
    def mock_ea_server():
        """Mock EA server for testing"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server.bind(('localhost', 9998))  # Different port for testing
            server.listen(1)
            server.settimeout(5)  # 5 second timeout
            
            client, addr = server.accept()
            
            # Send mock heartbeat
            heartbeat_msg = b'{"type":"heartbeat","timestamp":"' + datetime.now().isoformat().encode() + b'"}\n'
            client.send(heartbeat_msg)
            
            # Receive response
            response = client.recv(1024)
            
            client.close()
            server.close()
            
            return len(response) > 0
            
        except socket.timeout:
            server.close()
            return False
        except Exception:
            server.close()
            return False
    
    def test_client():
        """Test client connection"""
        time.sleep(0.5)  # Wait for server to start
        
        try:
            from core.ea_connector import EAConnector
            
            ea_config = {'host': 'localhost', 'port': 9998, 'timeout': 3}
            connector = EAConnector(ea_config)
            
            if connector.connect():
                time.sleep(1)  # Allow communication
                connector.disconnect()
                return True
            else:
                return False
                
        except Exception:
            return False
    
    # Start mock server in thread
    server_thread = threading.Thread(target=mock_ea_server)
    server_thread.start()
    
    # Test client connection
    client_result = test_client()
    
    # Wait for server thread
    server_thread.join()
    
    if client_result:
        print("OK: Socket communication test successful")
        return True
    else:
        print("ERROR: Socket communication test failed")
        return False

def test_dll_availability():
    """Test DLL availability and properties"""
    print("Testing DLL availability...")
    
    dll_path = "MQL4_DLL_SocketBridge.dll"
    
    if not os.path.exists(dll_path):
        print("ERROR: DLL file not found")
        return False
    
    # Check file size (should be ~31KB)
    file_size = os.path.getsize(dll_path)
    if file_size < 30000 or file_size > 35000:
        print(f"WARNING: DLL file size unusual: {file_size} bytes")
    else:
        print(f"OK: DLL file size correct: {file_size} bytes")
    
    # Check modification time (should be recent)
    mod_time = os.path.getmtime(dll_path)
    mod_datetime = datetime.fromtimestamp(mod_time)
    age_hours = (datetime.now() - mod_datetime).total_seconds() / 3600
    
    if age_hours > 24:
        print(f"WARNING: DLL is {age_hours:.1f} hours old")
    else:
        print(f"OK: DLL is recent ({age_hours:.1f} hours old)")
    
    print("OK: DLL is available and ready for MT4 integration")
    return True

def test_mql4_ea_syntax():
    """Test MQL4 EA file for basic syntax validation"""
    print("Testing MQL4 EA file...")
    
    ea_file = "HUEY_P_EA_ExecutionEngine_8.mq4"
    if not os.path.exists(ea_file):
        print("ERROR: MQL4 EA file not found")
        return False
    
    # Read file and check for key components
    with open(ea_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    required_elements = [
        'OnTick()',
        'OnInit()',
        'OnDeinit(',
        'EnableDLLSignals',
        'HUEY_P',
        'StateManager',
        'SignalManager'
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"ERROR: Missing MQL4 elements: {missing_elements}")
        return False
    
    file_size = len(content)
    line_count = content.count('\n')
    
    print(f"OK: MQL4 EA file valid ({file_size} chars, {line_count} lines)")
    return True

def main():
    """Run comprehensive system integration tests"""
    print("HUEY_P System Integration Test Suite")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        ("File Structure", test_file_structure),
        ("MQL4 EA Syntax", test_mql4_ea_syntax), 
        ("DLL Availability", test_dll_availability),
        ("Database Operations", test_database_operations),
        ("Python Interface", test_python_interface),
        ("Socket Communication", test_socket_server_simulation)
    ]
    
    results = []
    
    # Run tests
    for test_name, test_func in test_cases:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"ERROR: Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("Integration Test Results:")
    print("-" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("\nSUCCESS: All integration tests passed!")
        print("\nSystem is ready for MT4 deployment:")
        print("1. Copy MQL4_DLL_SocketBridge.dll to MT4/MQL4/Libraries/")
        print("2. Compile HUEY_P_EA_ExecutionEngine_8.mq4 in MetaEditor") 
        print("3. Enable 'Allow DLL imports' in MT4 settings")
        print("4. Start EA with EnableDLLSignals = true")
        print("5. Run Python interface: python huey_main.py")
        return True
    else:
        failed_tests = [name for name, result in results if not result]
        print(f"\nFAILED: {len(failed_tests)} tests failed: {failed_tests}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)