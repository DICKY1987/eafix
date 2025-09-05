#!/usr/bin/env python3
"""
Test connection to EA bridge on port 5555
"""

import socket
import sys

def test_connection(port=5555):
    try:
        print(f"Testing connection to localhost:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"SUCCESS: Port {port} is listening!")
            return True
        else:
            print(f"FAILED: Port {port} is not listening")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("HUEY_P Bridge Port Test")
    print("=" * 30)
    
    # Test both ports
    port_5555_ok = test_connection(5555)
    port_9999_ok = test_connection(9999)
    
    print(f"\nResults:")
    print(f"Port 5555 (EA configured): {'OK' if port_5555_ok else 'CLOSED'}")
    print(f"Port 9999 (Python expecting): {'OK' if port_9999_ok else 'CLOSED'}")
    
    if port_5555_ok:
        print("\nRECOMMENDATION: Change Python to use port 5555")
    elif port_9999_ok:
        print("\nRECOMMENDATION: Change EA to use port 9999")
    else:
        print("\nBridge is not listening on either port - check EA status")