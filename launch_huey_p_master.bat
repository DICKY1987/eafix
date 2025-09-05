@echo off
REM ====================================================================
REM HUEY_P Master Trading System Desktop Launcher
REM Automatically launches MT4 platform and Trading GUI
REM Copyright 2025, HUEY_P Trading Systems  
REM ====================================================================

title HUEY_P Master Trading System Launcher

echo.
echo ====================================================================
echo  🚀 HUEY_P Master Trading System Launcher
echo ====================================================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Set environment variables
set PYTHONPATH=%CD%;%CD%\src;%CD%\core;%CD%\tabs
set HUEY_P_HOME=%CD%

echo 📍 Working Directory: %CD%
echo 🐍 Python Path: %PYTHONPATH%
echo.

REM Step 1: Check if MT4 is already running
echo ⏳ Checking MetaTrader 4 status...
tasklist /FI "IMAGENAME eq terminal.exe" 2>NUL | find /I /N "terminal.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo ✅ MT4 is already running
) else (
    echo 🔍 MT4 not running - attempting to start...
    call :StartMT4
)

echo.

REM Step 2: Launch the GUI
echo 🎮 Starting HUEY_P Trading System GUI...
echo.

REM Try different launch methods in order of preference
if exist "launch_trading_system.py" (
    echo 📊 Launching main trading system interface...
    python launch_trading_system.py
) else if exist "launch_gui.bat" (
    echo 📱 Launching GUI via batch script...
    call launch_gui.bat
) else (
    echo 📋 Launching desktop application module...
    python -m eafix.apps.desktop.main
)

echo.
echo 🏁 HUEY_P Master Trading System session ended
pause
exit /b 0

REM ====================================================================
REM MT4 Auto-Launch Function
REM ====================================================================
:StartMT4
echo.
echo 🔍 Searching for MetaTrader 4 installation...

REM Common MT4 installation paths
set MT4_PATHS[0]="C:\Program Files (x86)\MetaTrader 4\terminal.exe"
set MT4_PATHS[1]="C:\Program Files\MetaTrader 4\terminal.exe"
set MT4_PATHS[2]="C:\MT4\terminal.exe"
set MT4_PATHS[3]="D:\Program Files (x86)\MetaTrader 4\terminal.exe"
set MT4_PATHS[4]="D:\Program Files\MetaTrader 4\terminal.exe"

REM Check for custom MT4_PATH environment variable
if defined MT4_PATH (
    if exist "%MT4_PATH%" (
        echo ✅ Found MT4 at custom path: %MT4_PATH%
        start "" "%MT4_PATH%"
        echo ⏳ Waiting for MT4 to initialize...
        timeout /t 5 /nobreak >nul
        goto :eof
    ) else (
        echo ⚠️  Custom MT4_PATH does not exist: %MT4_PATH%
    )
)

REM Search common installation directories
for /L %%i in (0,1,4) do (
    call :CheckMT4Path %%i
)

REM If not found in common paths, try registry search
echo 🔍 Searching Windows Registry for MT4...
for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall" /s /f "MetaTrader" 2^>nul ^| findstr "InstallLocation"') do (
    set "MT4_REG_PATH=%%b\terminal.exe"
    if exist "!MT4_REG_PATH!" (
        echo ✅ Found MT4 via registry: !MT4_REG_PATH!
        start "" "!MT4_REG_PATH!"
        echo ⏳ Waiting for MT4 to initialize...
        timeout /t 5 /nobreak >nul
        goto :eof
    )
)

echo.
echo ⚠️  MetaTrader 4 not found in standard locations
echo 💡 To auto-launch MT4, you can:
echo    1. Set environment variable: set MT4_PATH=C:\path\to\your\terminal.exe  
echo    2. Install MT4 in a standard location
echo    3. Start MT4 manually before running this launcher
echo.
echo 📋 Continuing with GUI launch...
goto :eof

REM ====================================================================
REM Helper function to check specific MT4 path
REM ====================================================================
:CheckMT4Path
setlocal enabledelayedexpansion
set index=%1
call set "path=%%MT4_PATHS[%index%]%%"
set path=%path:"=%
if exist "%path%" (
    echo ✅ Found MT4 at: %path%
    start "" "%path%"
    echo ⏳ Waiting for MT4 to initialize...
    timeout /t 5 /nobreak >nul
    endlocal
    goto :eof
)
endlocal
goto :eof

REM ====================================================================
REM Error Handler
REM ====================================================================
:Error
echo.
echo ❌ Error occurred during launch
echo 📋 Check the following:
echo    - Python is installed and in PATH
echo    - Required dependencies are installed
echo    - HUEY_P system files are present
echo.
pause
exit /b 1