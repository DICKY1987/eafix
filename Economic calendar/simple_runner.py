#!/usr/bin/env python3
"""
Simple One-Click ForexFactory Calendar Processor
Just run this script and it does everything automatically!

Usage: python run_calendar.py
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['selenium', 'pandas', 'webdriver_manager']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Installing required packages...")
        for package in missing_packages:
            os.system(f"pip install {package}")
        print("✅ Dependencies installed!")

def main():
    """Main runner - keeps it simple!"""
    
    print("🚀 ForexFactory Calendar Auto-Processor")
    print("=" * 50)
    
    # Check dependencies first
    check_dependencies()
    
    # Import the main system (after dependencies are installed)
    try:
        # Add the current directory to Python path
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        # Import our automated system
        from ff_auto_downloader import AutomatedCalendarSystem, Config
        
        # Simple configuration - user can customize if needed
        config = Config()
        
        # Create output directory if it doesn't exist
        output_dir = Path("./trading_calendar_output")
        output_dir.mkdir(exist_ok=True)
        config.OUTPUT_PATH = output_dir
        
        print(f"📁 Output directory: {output_dir.absolute()}")
        
        # Initialize and run the system
        print("🔄 Starting automated download and processing...")
        calendar_system = AutomatedCalendarSystem(config)
        
        # Run the complete process
        result_file = calendar_system.run_automated_process()
        
        if result_file:
            print("=" * 50)
            print("✅ SUCCESS! Calendar processed successfully!")
            print(f"📄 Ready-to-trade CSV saved to:")
            print(f"   {result_file.absolute()}")
            print()
            print("📋 What was processed:")
            print("   • Downloaded latest ForexFactory calendar")
            print("   • Filtered to High/Medium impact events only")
            print("   • Created anticipation events (1h, 2h, 4h before)")
            print("   • Added equity market opening events")
            print("   • Generated strategy IDs")
            print("   • Exported MT4-compatible format")
            print()
            print("🎯 Next steps:")
            print("   1. Copy the CSV file to your MT4 system")
            print("   2. Configure your EA to read this file")
            print("   3. Start automated trading!")
            print()
            print("⏰ To run automatically every Sunday at 12 PM:")
            print("   python ff_auto_downloader.py --schedule")
            
        else:
            print("❌ FAILED! Could not process calendar.")
            print("   Check the log file for details: calendar_downloader.log")
            print("   Common issues:")
            print("   • Internet connection problems")
            print("   • ForexFactory website changes")
            print("   • Chrome browser not installed")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure ff_auto_downloader.py is in the same directory")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("   Check the log file for details: calendar_downloader.log")
    
    # Keep window open so user can see results
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
