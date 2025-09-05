#!/usr/bin/env python3
"""
Simple socket connection test for HUEY_P system
Tests both socket communication and CSV fallback
"""

import socket
import time
import csv
import json
from datetime import datetime
import os

def test_socket_connection(host='localhost', port=5555, timeout=5):
    """Test socket connection to MT4 EA"""
    print(f"Testing socket connection to {host}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        
        if result == 0:
            print("OK: Socket connection SUCCESSFUL")
            
            # Send test message
            test_message = {
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "data": "test_connection"
            }
            
            try:
                sock.send(json.dumps(test_message).encode('utf-8'))
                print("OK: Test message sent successfully")
                
                # Try to receive response
                sock.settimeout(2)
                response = sock.recv(1024)
                if response:
                    print(f"OK: Received response: {response.decode('utf-8')}")
                else:
                    print("WARN: No response received (expected for one-way communication)")
                    
            except socket.timeout:
                print("WARN: No response received (timeout - may be normal)")
            except Exception as e:
                print(f"WARN: Error sending/receiving: {e}")
                
        else:
            print(f"FAIL: Socket connection FAILED (Error: {result})")
            
        sock.close()
        return result == 0
        
    except Exception as e:
        print(f"FAIL: Socket test failed: {e}")
        return False

def test_csv_communication():
    """Test CSV-based communication fallback"""
    print("\nTesting CSV communication fallback...")
    
    # Test file paths
    mt4_path = r"C:\Users\Richard Wilks\AppData\Roaming\MetaQuotes\Terminal\F2262CFAFF47C27887389DAB2852351A"
    signals_file = os.path.join(mt4_path, "eafix", "trading_signals.csv")
    responses_file = os.path.join(mt4_path, "eafix", "trade_responses.csv")
    
    try:
        # Test writing a signal
        test_signal = {
            "signal_id": f"TEST_{int(time.time())}",
            "symbol": "EURUSD",
            "direction": "BUY", 
            "lot_size": 0.01,
            "stop_loss": 20,
            "take_profit": 40,
            "comment": "CSV_TEST",
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.75,
            "strategy_id": 12345
        }
        
        # Write signal to CSV
        with open(signals_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'signal_id', 'symbol', 'direction', 'lot_size', 'stop_loss', 
                'take_profit', 'comment', 'timestamp', 'confidence', 'strategy_id'
            ])
            writer.writerow([
                test_signal['signal_id'], test_signal['symbol'], test_signal['direction'],
                test_signal['lot_size'], test_signal['stop_loss'], test_signal['take_profit'],
                test_signal['comment'], test_signal['timestamp'], test_signal['confidence'],
                test_signal['strategy_id']
            ])
        
        print(f"OK: Test signal written to: {signals_file}")
        
        # Check if responses file exists and is accessible
        if os.path.exists(responses_file):
            with open(responses_file, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                print(f"OK: Responses file accessible ({len(rows)} rows)")
        else:
            print(f"INFO: Responses file doesn't exist yet: {responses_file}")
            
        return True
        
    except Exception as e:
        print(f"FAIL: CSV communication test failed: {e}")
        return False

def test_mt4_terminal():
    """Check if MT4 terminal is running"""
    print("\nChecking MT4 Terminal status...")
    
    try:
        import subprocess
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal.exe'], 
                              capture_output=True, text=True)
        
        if 'terminal.exe' in result.stdout:
            print("OK: MT4 Terminal is running")
            return True
        else:
            print("FAIL: MT4 Terminal is not running")
            return False
            
    except Exception as e:
        print(f"WARN: Could not check MT4 status: {e}")
        return False

def test_dll_availability():
    """Check if DLL is available in MT4 Libraries folder"""
    print("\nChecking DLL availability...")
    
    dll_path = r"C:\Users\Richard Wilks\AppData\Roaming\MetaQuotes\Terminal\F2262CFAFF47C27887389DAB2852351A\MQL4\Libraries\MQL4_DLL_SocketBridge.dll"
    
    if os.path.exists(dll_path):
        file_size = os.path.getsize(dll_path)
        print(f"OK: DLL found at: {dll_path} ({file_size} bytes)")
        return True
    else:
        print(f"FAIL: DLL not found at: {dll_path}")
        return False

def main():
    """Run all communication tests"""
    print("HUEY_P Communication System Test")
    print("=" * 50)
    
    # Run all tests
    results = {}
    results['mt4_running'] = test_mt4_terminal()
    results['dll_available'] = test_dll_availability()
    results['socket_5555'] = test_socket_connection('localhost', 5555)
    results['socket_9999'] = test_socket_connection('localhost', 9999)  # Alternative port
    results['csv_communication'] = test_csv_communication()
    
    # Summary
    print("\n" + "=" * 50)
    print("COMMUNICATION TEST SUMMARY")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "OK: PASS" if result else "FAIL: FAIL"
        print(f"{test_name:20}: {status}")
    
    # Recommendations
    print("\n" + "=" * 50)
    print("RECOMMENDATIONS")
    print("=" * 50)
    
    if results['socket_5555'] or results['socket_9999']:
        print("OK: Socket communication is working!")
        print("   Configure EA with: EnableDLLSignals = true")
    elif results['csv_communication']:
        print("WARN: Socket communication failed, but CSV fallback is available")
        print("   Configure EA with: EnableDLLSignals = false, EnableCSVSignals = true")
        print("   EA must have: AutonomousMode = false (to read signals)")
    else:
        print("FAIL: Both socket and CSV communication have issues")
        print("   Check MT4 EA configuration and file permissions")
    
    if not results['mt4_running']:
        print("FAIL: Start MT4 Terminal and load HUEY_P EA")
    
    if not results['dll_available']:
        print("FAIL: Copy MQL4_DLL_SocketBridge.dll to MT4\\MQL4\\Libraries\\")

if __name__ == "__main__":
    main()