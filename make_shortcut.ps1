# HUEY_P Desktop Shortcut Creator

Write-Host "Creating HUEY_P Master Trading System Desktop Shortcut..."

# Get paths
$ScriptDir = $PSScriptRoot
$LauncherPath = Join-Path $ScriptDir "launch_huey_p_master.bat"
$DesktopPath = [Environment]::GetFolderPath("Desktop")  
$ShortcutPath = Join-Path $DesktopPath "HUEY_P Master Trading System.lnk"

# Check if launcher exists
if (-not (Test-Path $LauncherPath)) {
    Write-Host "Error: Launcher not found at $LauncherPath"
    exit 1
}

# Create shortcut
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $LauncherPath
    $Shortcut.WorkingDirectory = $ScriptDir
    $Shortcut.Description = "HUEY_P Master Trading System - Auto-launches MT4 and GUI"
    $Shortcut.Save()
    
    Write-Host "SUCCESS: Desktop shortcut created!"
    Write-Host "Location: $ShortcutPath"
    Write-Host "Double-click the desktop shortcut to launch HUEY_P with MT4!"
    
} catch {
    Write-Host "Error creating shortcut: $($_.Exception.Message)"
    exit 1
}