"""
Launch script for HUEY_P Modern GUI
Integrates with existing trading system
"""

import sys
import os
from pathlib import Path

def main():
    """Launch the modern HUEY_P GUI"""
    
    print("Launching HUEY_P Modern GUI...")
    print("=" * 50)
    
    # Check if GUI directory exists
    gui_path = Path(__file__).parent / "huey_p_gui"
    if not gui_path.exists():
        print("ERROR: huey_p_gui directory not found!")
        print("Please run the setup script first.")
        return 1
    
    # Add GUI path to Python path
    sys.path.insert(0, str(gui_path))
    
    try:
        # Import and run the modern GUI
        from main_app import main as run_gui
        
        print("Modern GUI components loaded successfully")
        print("Event bus and state manager initialized")
        print("Theme system activated")
        print("\nStarting Modern HUEY_P Trading Interface...")
        print("   - Risk monitoring ribbon active")
        print("   - Real-time updates enabled") 
        print("   - Emergency controls available")
        print("   - Dark theme applied")
        print("\n" + "=" * 50)
        
        # Run the GUI
        run_gui()
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("\nPossible solutions:")
        print("   1. Install missing dependencies:")
        print("      pip install customtkinter ttkbootstrap")
        print("   2. Check if all GUI components are present")
        return 1
    except Exception as e:
        print(f"Error launching GUI: {e}")
        return 1
    
    print("\nHUEY_P Modern GUI closed.")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)