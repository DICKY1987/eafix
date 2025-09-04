"""
Main application launcher for MT4 DDE Price Import Interface
"""
import sys
import os
import logging
import traceback
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_logging():
    """Setup application logging"""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'dde_interface_{datetime.now().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def check_dependencies():
    """Check if required dependencies are available"""
    missing_deps = []
    
    try:
        import tkinter
    except ImportError:
        missing_deps.append('tkinter')
    
    try:
        import numpy
    except ImportError:
        missing_deps.append('numpy')
    
    try:
        import pandas
    except ImportError:
        missing_deps.append('pandas')
    
    try:
        import matplotlib
    except ImportError:
        missing_deps.append('matplotlib')
    
    try:
        import win32ui
        import win32con
        import dde
    except ImportError:
        missing_deps.append('pywin32 (for DDE functionality)')
    
    return missing_deps


def main():
    """Main application entry point"""
    logger = setup_logging()
    logger.info("Starting MT4 DDE Price Import Interface")
    
    try:
        # Check dependencies
        missing_deps = check_dependencies()
        if missing_deps:
            error_msg = f"Missing required dependencies: {', '.join(missing_deps)}"
            logger.error(error_msg)
            
            # Show error dialog if tkinter is available
            if 'tkinter' not in missing_deps:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Missing Dependencies", 
                                   f"{error_msg}\n\nPlease install missing packages using:\n"
                                   f"pip install {' '.join(missing_deps)}")
                root.destroy()
            else:
                print(error_msg)
                print("Please install missing packages using pip")
            
            return 1
        
        # Import main application
        from main_tab import DDEPriceImportApp
        
        logger.info("Dependencies verified, launching application...")
        
        # Create and run application
        app = DDEPriceImportApp()
        app.run()
        
        logger.info("Application closed normally")
        return 0
        
    except Exception as e:
        logger.error(f"Critical error starting application: {e}")
        logger.error(traceback.format_exc())
        
        # Try to show error dialog
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Application Error", 
                               f"Failed to start application:\n{e}\n\nCheck logs for details.")
            root.destroy()
        except:
            print(f"Critical error: {e}")
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)