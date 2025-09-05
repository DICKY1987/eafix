@echo off
REM ====================================================================
REM HUEY_P Desktop Shortcut Setup - Simple Batch Launcher
REM Runs the PowerShell script to create desktop shortcut
REM ====================================================================

title HUEY_P Desktop Shortcut Setup

echo.
echo ====================================================================
echo  🖥️  HUEY_P Desktop Shortcut Setup
echo ====================================================================
echo.
echo This will create a desktop shortcut for HUEY_P Master Trading System
echo The shortcut will automatically launch MT4 and the trading GUI.
echo.

REM Check if we're in the right directory
if not exist "launch_huey_p_master.bat" (
    echo ❌ Error: Please run this script from the HUEY_P project directory
    echo Expected files: launch_huey_p_master.bat, create_desktop_shortcut.ps1
    echo Current directory: %CD%
    echo.
    pause
    exit /b 1
)

echo 📁 Working in: %CD%
echo.

REM Check PowerShell availability
powershell -Command "Write-Host 'PowerShell is available'" >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: PowerShell is not available
    echo Please install PowerShell to use this setup script.
    echo.
    pause
    exit /b 1
)

echo ⏳ Running PowerShell script to create desktop shortcut...
echo.

REM Run the PowerShell script
powershell -ExecutionPolicy Bypass -File "create_desktop_shortcut.ps1"

if errorlevel 1 (
    echo.
    echo ❌ Error: Failed to create desktop shortcut
    echo Please check the error messages above.
) else (
    echo.
    echo ✅ Desktop shortcut setup completed successfully!
    echo.
    echo 🎮 You can now launch HUEY_P Master Trading System from:
    echo    • Desktop shortcut: "HUEY_P Master Trading System"
    echo    • Start Menu: Programs ^> HUEY_P Trading
    echo.
)

echo.
echo 📋 Press any key to exit...
pause >nul