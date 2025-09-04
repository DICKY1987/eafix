#!/usr/bin/env python3
"""
Integration Test for MVP Trading System
Tests signal generation and basic database setup
"""

import subprocess
import os
from pathlib import Path

def test_signal_generator():
    print("▶ Testing signal_generator.py...")
    result = subprocess.run(["python3", "Python/signal_generator.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("❌ Signal generator failed.")
        return False
    return True

def test_database_initialization():
    print("▶ Testing init_database.py...")
    result = subprocess.run(["python3", "Database/init_database.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("❌ Database initialization failed.")
        return False
    return True

if __name__ == "__main__":
    print("🚦 Starting integration tests...")
    signal_ok = test_signal_generator()
    db_ok = test_database_initialization()
    if signal_ok and db_ok:
        print("✅ Integration tests passed.")
    else:
        print("❌ Integration tests failed.")
