#!/usr/bin/env python3
"""
Test script to verify DLL exports and basic functionality
Run this after building the DLL to test the exported functions
"""

import ctypes
import os
import sys
import time
import socket
import threading

def test_dll_exports():
    """Test that the DLL can be loaded and all required functions are exported"""
    
    dll_path = "./build/Release/MQL4_DLL_SocketBridge.dll"
    
    if not os.path.exists(dll_path):
        print(f"❌ DLL not found at: {dll_path}")
        print("Please build the DLL first using build_dll.bat")
        return False
    
    try:
        # Load the DLL
        dll = ctypes.WinDLL(dll_path)
        print(f"✅ DLL loaded successfully: {dll_path}")
        
        # Test each exported function
        functions = [
            ('StartServer', [ctypes.c_int, ctypes.c_int, ctypes.c_int], ctypes.c_int),
            ('StopServer', [], None),
            ('GetLastMessage', [ctypes.c_char_p, ctypes.c_int], ctypes.c_int),
            ('GetCommunicationStatus', [], ctypes.c_int),
            ('SocketIsConnected', [ctypes.c_int], ctypes.c_bool),
            ('GetLastSocketError', [], ctypes.c_char_p),
            ('SocketSendHeartbeat', [ctypes.c_int], ctypes.c_bool),
            ('SendMessageToClient', [ctypes.c_char_p], ctypes.c_bool),
            ('GetConnectedClientCount', [], ctypes.c_int),
            ('SetDebugMode', [ctypes.c_bool], None)
        ]
        
        for func_name, argtypes, restype in functions:
            try:
                func = getattr(dll, func_name)
                func.argtypes = argtypes
                func.restype = restype
                print(f"✅ Function exported: {func_name}")
            except AttributeError:
                print(f"❌ Function missing: {func_name}")
                return False
        
        print("\n🎉 All required functions are properly exported!")
        return True
        
    except Exception as e:
        print(f"❌ Error loading DLL: {e}")
        return False

def test_basic_functionality():
    """Test basic DLL functionality"""
    
    dll_path = "./build/Release/MQL4_DLL_SocketBridge.dll"
    
    try:
        dll = ctypes.WinDLL(dll_path)
        
        # Set up function signatures
        dll.StartServer.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        dll.StartServer.restype = ctypes.c_int
        
        dll.GetCommunicationStatus.restype = ctypes.c_int
        dll.GetConnectedClientCount.restype = ctypes.c_int
        dll.SocketIsConnected.argtypes = [ctypes.c_int]
        dll.SocketIsConnected.restype = ctypes.c_bool
        
        dll.GetLastMessage.argtypes = [ctypes.c_char_p, ctypes.c_int]
        dll.GetLastMessage.restype = ctypes.c_int
        
        dll.SendMessageToClient.argtypes = [ctypes.c_char_p]
        dll.SendMessageToClient.restype = ctypes.c_bool
        
        dll.SetDebugMode.argtypes = [ctypes.c_bool]
        dll.StopServer.restype = None
        
        print("\n🧪 Testing Basic Functionality...")
        
        # Enable debug mode
        dll.SetDebugMode(True)
        print("✅ Debug mode enabled")
        
        # Test starting server
        result = dll.StartServer(5556, 0, 0)  # Use different port for testing
        if result == 1:  # STATUS_CONNECTED
            print("✅ Server started successfully on port 5556")
        else:
            print(f"❌ Failed to start server, result: {result}")
            return False
        
        # Check status
        status = dll.GetCommunicationStatus()
        print(f"✅ Communication status: {status}")
        
        # Check client count (should be 0)
        client_count = dll.GetConnectedClientCount()
        print(f"✅ Connected clients: {client_count}")
        
        # Test client connection
        print("\n📡 Testing client connection...")
        
        def test_client():
            time.sleep(0.5)  # Wait for server to be ready
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect(('localhost', 5556))
                print("✅ Client connected successfully")
                
                # Send a test message
                test_message = b"Hello from test client"
                client_socket.send(test_message)
                print(f"✅ Message sent: {test_message}")
                
                # Keep connection open for a bit
                time.sleep(2)
                
                client_socket.close()
                print("✅ Client disconnected")
                
            except Exception as e:
                print(f"❌ Client connection failed: {e}")
        
        # Start client in separate thread
        client_thread = threading.Thread(target=test_client)
        client_thread.start()
        
        # Wait for client to connect and check status
        time.sleep(1)
        
        client_count = dll.GetConnectedClientCount()
        print(f"✅ Connected clients after connection: {client_count}")
        
        is_connected = dll.SocketIsConnected(0)
        print(f"✅ Socket connected: {is_connected}")
        
        # Test message retrieval
        buffer = ctypes.create_string_buffer(4096)
        msg_length = dll.GetLastMessage(buffer, 4096)
        if msg_length > 0:
            message = buffer.value.decode('utf-8')
            print(f"✅ Message received: {message}")
        
        # Test sending message to client
        test_response = b"Hello from DLL server"
        send_result = dll.SendMessageToClient(test_response)
        print(f"✅ Message send result: {send_result}")
        
        # Wait for client thread to finish
        client_thread.join()
        
        # Stop server
        dll.StopServer()
        print("✅ Server stopped")
        
        print("\n🎉 Basic functionality tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def main():
    print("🔧 MQL4_DLL_SocketBridge Test Suite")
    print("=" * 50)
    
    # Test 1: DLL Export Verification
    print("\n1️⃣ Testing DLL Exports...")
    exports_ok = test_dll_exports()
    
    if not exports_ok:
        print("\n❌ Export tests failed. Cannot proceed with functionality tests.")
        return False
    
    # Test 2: Basic Functionality
    print("\n2️⃣ Testing Basic Functionality...")
    functionality_ok = test_basic_functionality()
    
    if functionality_ok:
        print("\n🏆 All tests passed! The DLL is ready for use.")
        print("\n📋 Next steps:")
        print("1. Copy MQL4_DLL_SocketBridge.dll to your MT4/MQL4/Libraries/ folder")
        print("2. Enable 'Allow DLL imports' in MT4 Expert Advisor settings")
        print("3. Load the HUEY_P Expert Advisor with EnableDLLSignals = true")
        print("4. Start the Python interface with: python huey_main.py")
        return True
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
        return False

if __name__ == "__main__":
    if sys.platform != "win32":
        print("❌ This test script is for Windows only (requires WinDLL)")
        sys.exit(1)
    
    success = main()
    sys.exit(0 if success else 1)