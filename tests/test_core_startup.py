#!/usr/bin/env python3
"""
Test core component startup without full GUI
"""

import sys
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test database connectivity"""
    print("Testing database connection...")
    
    try:
        from core.database_manager import DatabaseManager
        
        db_config = {'path': 'Database/trading_system.db'}
        db_manager = DatabaseManager(db_config)
        if db_manager.connect():
            print("OK: Database connection successful")
            
            # Test basic query
            trades = db_manager.get_recent_trades()
            print(f"OK: Recent trades query successful: {len(trades)} records")
            
            db_manager.disconnect()
            return True
        else:
            print("ERROR: Database connection failed")
            return False
            
    except Exception as e:
        print(f"ERROR: Database test failed: {e}")
        return False

def test_ea_connector():
    """Test EA connector without UI"""
    print("Testing EA connector...")
    
    try:
        from core.ea_connector import EAConnector
        
        # Test basic initialization (won't connect without MT4)
        ea_config = {'host': 'localhost', 'port': 9999}
        ea_connector = EAConnector(ea_config)
        print("OK: EA connector initialized")
        
        # Test connection attempt (expected to fail without MT4)
        if ea_connector.connect():
            print("OK: EA connector connected (unexpected - MT4 not running)")
            ea_connector.disconnect()
        else:
            print("OK: EA connector connection failed as expected (MT4 not running)")
            
        return True
        
    except Exception as e:
        print(f"ERROR: EA connector test failed: {e}")
        return False

def test_data_models():
    """Test data model classes"""
    print("Testing data models...")
    
    try:
        from core.data_models import SystemStatus, LiveMetrics, TradeData
        
        # Test SystemStatus
        status = SystemStatus()
        status.database_connected = True
        print("OK: SystemStatus model working")
        
        # Test LiveMetrics
        metrics = LiveMetrics()
        metrics.account_balance = 10000.0
        print("OK: LiveMetrics model working")
        
        # Test TradeData (requires parameters)
        from core.data_models import OrderType
        trade = TradeData(
            ticket=12345,
            symbol="EURUSD", 
            order_type=OrderType.BUY,
            volume=0.1,
            open_price=1.1000
        )
        print("OK: TradeData model working")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Data models test failed: {e}")
        return False

def main():
    print("HUEY_P Core Components Test")
    print("=" * 40)
    
    results = []
    
    # Test 1: Data Models
    results.append(("Data Models", test_data_models()))
    
    # Test 2: Database
    results.append(("Database", test_database_connection()))
    
    # Test 3: EA Connector
    results.append(("EA Connector", test_ea_connector()))
    
    # Summary
    print("\nTest Results:")
    print("-" * 20)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("\nSUCCESS: All core components are working!")
        return True
    else:
        print(f"\nWARNING: Some components failed ({len(results) - passed} failures)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)