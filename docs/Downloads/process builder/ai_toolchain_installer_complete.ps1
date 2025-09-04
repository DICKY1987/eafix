# File: ai_toolchain_installer_complete.ps1
# Version: Complete Unified v2.1
# Purpose: One-shot Windows AI dev workstation bootstrap (admin-optional)
# Features: winget-first installs, Python venv + pinned deps, guardrails pre-commit,
#           Compose v2 (Redis + Ollama), safer .env handling, robust logging,
#           preflight checks, retries, post-install doctor, optional compose up,
#           optional GitHub auth login.
# Usage:   Run from a PowerShell terminal (preferably Windows Terminal).
#          Examples:
#            pwsh -File .\ai_toolchain_installer_complete.ps1 -Verbose
#            pwsh -File .\ai_toolchain_installer_complete.ps1 -DryRun -StartCompose -LoginGh
#
# Exit codes: 0 success; non-zero on failure.

<#
.SYNOPSIS
    Installs AI toolchain dependencies with validation, logging, and safe execution.

.DESCRIPTION
    Validates paths and parameters, handles external process execution safely,
    cleans up properly, and logs events with customizable verbosity.
    Supports winget-first installs, Python venv with pinned dependencies,
    guardrails pre-commit hooks, Docker Compose stack (Redis + Ollama),
    and comprehensive preflight checks with retries.

.PARAMETER ConfigPath
    Path to the AI configuration file (default: ".ai\ai-config.json").

.PARAMETER LogLevel
    Defines logging level: DEBUG, INFO, WARNING, ERROR (default: INFO).

.PARAMETER DryRun
    Simulate actions without making changes.

.PARAMETER Force
    Forces overwrite of conflicting installations.

.PARAMETER InstallDocker
    Triggers Docker installation (override config; best effort if not admin).

.PARAMETER StartCompose
    Auto bring up compose stack if Docker is ready.

.PARAMETER LoginGh
    Ensure GitHub CLI authentication is completed.

.EXAMPLE
    .\ai_toolchain_installer_complete.ps1 -ConfigPath ".ai\config.json" -LogLevel DEBUG -DryRun

.EXAMPLE
    .\ai_toolchain_installer_complete.ps1 -StartCompose -LoginGh -Force
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [ValidateScript({
        $base = Split-Path $_
        return (Test-Path $base -PathType Container) -or ($base -eq '')
    })]
    [string]$ConfigPath = ".ai\ai-config.json",

    [Parameter(Mandatory = $false)]
    [ValidateSet('DEBUG','INFO','WARNING','ERROR')]
    [string]$LogLevel = 'INFO',

    [switch]$DryRun,
    [switch]$Force,
    [switch]$InstallDocker,  # override config; best effort if not admin
    [switch]$StartCompose,   # auto bring up compose stack if Docker ready
    [switch]$LoginGh         # ensure gh auth login is completed
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# ------------------------------------------------------------
# Globals & Paths
# ------------------------------------------------------------
$ScriptRoot = Split-Path -Parent ($MyInvocation.MyCommand.Path)
$RepoRoot   = Resolve-Path -Path (Join-Path $ScriptRoot '.')
$AiDir      = Join-Path $RepoRoot '.ai'
$LogDir     = Join-Path $AiDir 'logs'
$GuardDir   = Join-Path $AiDir 'guard'
$DockerDir  = Join-Path $AiDir 'docker'
$VenvPath   = Join-Path $AiDir '.venv'
$ReqPath    = Join-Path $AiDir 'requirements.txt'
$EnvPath    = Join-Path $RepoRoot '.env'
$GitIgnore  = Join-Path $RepoRoot '.gitignore'
$Quickstart = Join-Path $RepoRoot 'AI-Setup-QUICKSTART.md'
$TestPy     = Join-Path $AiDir 'test_imports.py'
$ProfileDir = Split-Path -Parent $PROFILE
$AliasesPs1 = Join-Path $AiDir 'cli_defaults.ps1'
$ComposeYml = Join-Path $DockerDir 'compose.yml'

# Ensure folders exist (no-op in DryRun)
if (-not $DryRun) {
    $null = New-Item -ItemType Directory -Force -Path $AiDir,$LogDir,$GuardDir,$DockerDir,$ProfileDir -ErrorAction SilentlyContinue
}
$Global:LogFile = Join-Path $LogDir ("setup-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".log")

# ------------------------------------------------------------
# Logging helpers
# ------------------------------------------------------------
$LevelOrder = @{ 'DEBUG'=0; 'INFO'=1; 'WARNING'=2; 'ERROR'=3 }

function Write-Log {
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [Parameter(Mandatory = $false)][ValidateSet('DEBUG','INFO','WARNING','ERROR')][string]$Level = 'INFO'
    )
    
    if ($LevelOrder[$Level] -lt $LevelOrder[$LogLevel]) { return }
    
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $line = "[$ts] [$Level] $Message"
    $fg = switch ($Level) { 
        'ERROR'   { 'Red' } 
        'WARNING' { 'Yellow' } 
        'INFO'    { 'Green' }
        default   { 'White' } 
    }
    
    Write-Host $line -ForegroundColor $fg
    
    if (-not $DryRun) {
        try { 
            Add-Content -Path $Global:LogFile -Value $line -Force 
        } catch { 
            # Silently continue if logging fails
        }
    }
}

function Invoke-Step {
    param([string]$Name, [scriptblock]$Action)
    Write-Log "→ $Name" 'INFO'
    if ($DryRun) { 
        Write-Log "(dry-run) Skipped: $Name" 'DEBUG'
        return 
    }
    try {
        & $Action
        Write-Log "✓ $Name" 'INFO'
    }
    catch {
        Write-Log "✗ Failed: $Name - $($_.Exception.Message)" 'ERROR'
        throw
    }
}

# ------------------------------------------------------------
# Env/Process helpers
# ------------------------------------------------------------
function Test-IsAdmin { 
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) 
}

function Invoke-RefreshEnv {
    try {
        if (Get-Command refreshenv -ErrorAction SilentlyContinue) { 
            refreshenv
            return 
        }
        if ($env:ChocolateyInstall) {
            $chocoBin = Join-Path $env:ChocolateyInstall 'bin\refreshenv.cmd'
            if (Test-Path $chocoBin) { 
                & $chocoBin
                return 
            }
        }
    } catch { 
        Write-Log "refreshenv failed: $($_.Exception.Message)" 'DEBUG' 
    }
}

function Ensure-Path([string]$PathToAdd) {
    if (-not $PathToAdd) { return }
    $current = [Environment]::GetEnvironmentVariable('Path','Process')
    if (-not $current.Split(';') -contains $PathToAdd) {
        $newPath = [System.String]::Join(';', $current.Split(';') + $PathToAdd)
        [Environment]::SetEnvironmentVariable('Path', $newPath, 'Process')
        Write-Log "PATH += $PathToAdd" 'DEBUG'
    }
}

function Invoke-SafeCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$Command,
        [string[]]$Arguments = @()
    )

    Write-Log "Preparing to run: $Command $($Arguments -join ' ')" 'DEBUG'

    if ($DryRun) {
        Write-Log "Dry-run: Would run $Command with args $($Arguments -join ' ')" 'INFO'
        return @{ Code = 0; Stdout = ""; Stderr = "" }
    }

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Command
    
    # Safely escape arguments to prevent injection
    $escapedArgs = $Arguments | ForEach-Object {
        if ($_.Contains('"') -or $_.Contains(' ') -or $_.Contains('&') -or $_.Contains('|')) {
            '"' + $_.Replace('"', '\"') + '"'
        } else {
            $_
        }
    }
    $psi.Arguments = [System.String]::Join(' ', $escapedArgs)
    
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true

    $process = $null
    try {
        $process = [System.Diagnostics.Process]::Start($psi)
        $stdout = $process.StandardOutput.ReadToEnd()
        $stderr = $process.StandardError.ReadToEnd()
        $process.WaitForExit()
        
        Write-Log "Output: $stdout" 'DEBUG'
        if ($stderr -and $process.ExitCode -ne 0) { 
            Write-Log "Error: $stderr" 'ERROR' 
        } elseif ($stderr) {
            Write-Log "Warning: $stderr" 'WARNING'
        }
        
        return @{ Code = $process.ExitCode; Stdout = $stdout; Stderr = $stderr }
    }
    catch {
        Write-Log "Failed to execute command: $_" 'ERROR'
        throw
    }
    finally {
        if ($process) { 
            $process.Dispose() 
        }
    }
}

function Assert-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) { 
        throw "Command not found: $Name" 
    }
}

# ------------------------------------------------------------
# Retry + Preflight
# ------------------------------------------------------------
function Invoke-WithRetry {
    param([scriptblock]$Action, [int]$Max=3, [int]$DelaySec=5, [string]$What='operation')
    for ($i=1; $i -le $Max; $i++) {
        try { 
            return & $Action 
        } catch {
            if ($i -eq $Max) { 
                throw "Failed $What after $Max attempts: $($_.Exception.Message)" 
            }
            Write-Log "Retry $i/$Max for $What: $($_.Exception.Message)" 'WARNING'
            Start-Sleep -Seconds $DelaySec
        }
    }
}

function Invoke-Preflight {
    Write-Log 'Running preflight checks…' 'INFO'
    $issues = @()
    
    # Internet reachability
    try { 
        if (-not (Test-Connection -ComputerName '8.8.8.8' -Count 1 -Quiet)) { 
            $issues += 'No basic internet connectivity' 
        } 
    } catch [System.Net.NetworkInformation.PingException] {
        $issues += 'Ping blocked; skipping connectivity check'
    } catch {
        $issues += "Connectivity test failed: $($_.Exception.Message)"
    }
    
    # TLS reachability to key hosts
    foreach ($h in 'pypi.org','files.pythonhosted.org','registry.npmjs.org','api.github.com','ghcr.io','mcr.microsoft.com') {
        try { 
            if (-not (Test-NetConnection -ComputerName $h -Port 443 -InformationLevel Quiet)) { 
                $issues += "Cannot reach $h:443" 
            } 
        } catch { 
            $issues += "Cannot test $h:443" 
        }
    }
    
    # Disk space (≥ 5 GB free on repo drive)
    try {
        $drive = (Split-Path $RepoRoot -Qualifier) -replace ':',''
        $free  = (Get-PSDrive -Name $drive).Free
        if ($free -lt 5GB) { 
            $issues += 'Less than 5 GB free disk space' 
        }
    } catch { 
        Write-Log 'Disk space check failed; continuing.' 'WARNING' 
    }
    
    # Proxy hint
    if (-not $env:HTTPS_PROXY -and -not $env:HTTP_PROXY) { 
        Write-Log 'No HTTP(S)_PROXY set. If behind a corporate proxy, set it to avoid failures.' 'WARNING' 
    }
    
    if ($issues.Count -gt 0) {
        $issues | ForEach-Object { Write-Log $_ 'WARNING' }
        if (-not $Force) {
            throw "Preflight issues detected: $($issues -join '; '). Use -Force to continue anyway."
        }
    }
    
    Write-Log 'Preflight OK.' 'INFO'
}

# ------------------------------------------------------------
# Config: create or load
# ------------------------------------------------------------
$DefaultConfig = @{
    python_version = '3.11'
    node_channel   = 'LTS'
    install        = @{ docker = $false; ollama = $true }
    python_requirements = @{
        'pip'                 = '>=24.0'
        'setuptools'          = '>=70.0'
        'wheel'               = '>=0.43'
        'pydantic'            = '==2.7.4'
        'httpx'               = '==0.27.0'
        'tenacity'            = '==8.4.1'
        'numpy'               = '==1.26.4'
        'pandas'              = '==2.2.2'
        'redis'               = '==5.0.4'
        'fastapi'             = '==0.111.0'
        'uvicorn'             = '==0.30.1'
        'typer'               = '==0.12.3'
        'PyYAML'              = '==6.0.1'
        'tiktoken'            = '==0.7.0'
        'openai'              = '==1.40.0'
        'anthropic'           = '==0.34.2'
        'langchain'           = '==0.2.6'
        'langchain-community' = '==0.2.6'
        'langgraph'           = '==0.2.29'
        'duckdb'              = '==1.0.0'
    }
}

function Load-AIConfig {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$ConfigPath
    )

    Write-Log "Loading configuration from: $ConfigPath" 'INFO'

    if (-not (Test-Path $ConfigPath)) {
        Write-Log "Configuration file not found: $ConfigPath" 'ERROR'
        throw "Missing configuration file: $ConfigPath"
    }

    try {
        $configContent = Get-Content -Path $ConfigPath -Raw | ConvertFrom-Json
        Write-Log "Configuration loaded successfully." 'DEBUG'
        return $configContent
    } catch {
        Write-Log "Failed to parse configuration file: $($_.Exception.Message)" 'ERROR'
        throw
    }
}

Invoke-Step "Ensure config exists at $ConfigPath" {
    if (-not (Test-Path $ConfigPath)) {
        $json = ($DefaultConfig | ConvertTo-Json -Depth 6)
        $dir  = Split-Path -Parent $ConfigPath
        if ($dir) { 
            New-Item -ItemType Directory -Force -Path $dir | Out-Null 
        }
        Set-Content -Path $ConfigPath -Value $json -Encoding UTF8
    }
}

# Load config
$Config = Load-AIConfig -ConfigPath $ConfigPath
if ($InstallDocker) { $Config.install.docker = $true }
$Admin = Test-IsAdmin
Write-Log "Admin: $Admin | DryRun: $DryRun | Log: $Global:LogFile" 'DEBUG'

# ------------------------------------------------------------
# Preflight
# ------------------------------------------------------------
Invoke-Step 'Preflight checks' { Invoke-Preflight }

# ------------------------------------------------------------
# Environment Initialization
# ------------------------------------------------------------
function Initialize-AIEnvironment {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][hashtable]$Config
    )

    Write-Log "Initializing AI toolchain environment..." 'INFO'

    $requiredDirs = @(
        Join-Path $AiDir "bin",
        Join-Path $AiDir "data",
        Join-Path $AiDir "logs"
    )

    foreach ($dir in $requiredDirs) {
        if (-not (Test-Path $dir)) {
            if ($DryRun) {
                Write-Log "Dry-run: Would create directory $dir" 'INFO'
            } else {
                New-Item -Path $dir -ItemType Directory -Force | Out-Null
                Write-Log "Created directory: $dir" 'INFO'
            }
        } else {
            Write-Log "Directory already exists: $dir" 'DEBUG'
        }
    }

    # Extend PATH
    $binPath = Join-Path $AiDir "bin"
    Ensure-Path $binPath
}

Invoke-Step 'Initialize AI Environment' { Initialize-AIEnvironment -Config $Config }

# ------------------------------------------------------------
# winget-first installers (per-user where possible)
# ------------------------------------------------------------
function Winget-IsInstalled([string]$id) {
    try {
        $r = Invoke-SafeCommand 'winget' @('list','--id', $id, '-e')
        return ($r.Stdout -match $id)
    } catch { 
        return $false 
    }
}

function Winget-Install([string]$id, [string]$scope='user') {
    if ($DryRun) { 
        Write-Log "winget install $id --scope $scope (dry-run)" 'INFO'
        return 
    }
    Invoke-WithRetry -What "winget install $id" -Action {
        $args = @('install','--id', $id, '-e','--silent','--accept-package-agreements','--accept-source-agreements')
        if ($scope) { 
            $args += @('--scope', $scope) 
        }
        $r = Invoke-SafeCommand 'winget' $args
        if ($r.Code -ne 0) { 
            throw "winget($id) exit $($r.Code): $($r.Stderr.Trim())" 
        }
    }
}

Invoke-Step 'Ensure winget is available' { Assert-Command 'winget' }

# Git
Invoke-Step 'Install Git (user scope if possible)' {
    if (-not (Winget-IsInstalled 'Git.Git')) { 
        Winget-Install 'Git.Git' 'user' 
    }
    Ensure-Path "$env:ProgramFiles\Git\cmd"
}

# GitHub CLI
Invoke-Step 'Install GitHub CLI' {
    if (-not (Winget-IsInstalled 'GitHub.cli')) { 
        Winget-Install 'GitHub.cli' 'user' 
    }
}

# NodeJS LTS
Invoke-Step 'Install Node.js (LTS)' {
    if (-not (Winget-IsInstalled 'OpenJS.NodeJS.LTS')) { 
        Winget-Install 'OpenJS.NodeJS.LTS' 'user' 
    }
    Ensure-Path "$env:ProgramFiles\nodejs"
}

# Python specific version (user)
Invoke-Step ("Install Python " + $Config.python_version) {
    $pyId = if ($Config.python_version -like '3.11*') { 
        'Python.Python.3.11' 
    } elseif ($Config.python_version -like '3.12*') { 
        'Python.Python.3.12' 
    } else { 
        'Python.Python.3.11' 
    }
    if (-not (Winget-IsInstalled $pyId)) { 
        Winget-Install $pyId 'user' 
    }
}

Invoke-Step 'Refresh environment (PATH) safely' { Invoke-RefreshEnv }

# ------------------------------------------------------------
# Venv + pinned requirements
# ------------------------------------------------------------
function Resolve-PyForVersion([string]$ver) {
    # Try "py -3.x" first, then python from PATH
    try {
        $r = Invoke-SafeCommand 'py' @('-' + $ver, '--version')
        if ($r.Code -eq 0) { 
            return @('py', '-' + $ver) 
        }
    } catch {}
    return @('python')
}

$PyCmd = Resolve-PyForVersion $Config.python_version

Invoke-Step "Create venv at $VenvPath" {
    if (-not (Test-Path $VenvPath) -or $Force) {
        & $PyCmd[0] $PyCmd[1] '-m' 'venv' $VenvPath
    }
}

$PyExe  = Join-Path $VenvPath 'Scripts\python.exe'
$PipExe = @($PyExe,'-m','pip')

Invoke-Step 'Upgrade pip/setuptools/wheel' {
    Invoke-WithRetry -What 'pip upgrade' -Action { 
        & $PyExe -m pip install --upgrade pip setuptools wheel 
    }
}

# Write requirements.txt from config pins
Invoke-Step "Write pinned requirements.txt => $ReqPath" {
    $lines = @()
    foreach ($k in $Config.python_requirements.PSObject.Properties.Name) {
        $lines += "$k$($Config.python_requirements.$k)"
    }
    Set-Content -Path $ReqPath -Value ($lines -join "`n") -Encoding UTF8
}

Invoke-Step 'Install project Python requirements' {
    Invoke-WithRetry -What 'pip install -r requirements.txt' -Action {
        & $PyExe -m pip install --upgrade --upgrade-strategy eager -r $ReqPath
    }
}

# ------------------------------------------------------------
# .env and .gitignore safety
# ------------------------------------------------------------
Invoke-Step 'Ensure .env exists and is git-ignored' {
    if (-not (Test-Path $EnvPath)) {
        $envTemplate = @(
            '# API Keys (leave blank to fill later)',
            'OPENAI_API_KEY=',
            'ANTHROPIC_API_KEY=',
            'GROQ_API_KEY=',
            '',
            '# Services',
            'REDIS_URL=redis://localhost:6379/0'
        ) -join "`n"
        Set-Content -Path $EnvPath -Value $envTemplate -Encoding UTF8
    }
    
    $giLines = @('.env','.ai/logs/','.ai/.venv/','.ai/guard/')
    if (Test-Path $GitIgnore) {
        $existing = Get-Content $GitIgnore -ErrorAction SilentlyContinue
        $toAdd = $giLines | Where-Object { $_ -notin $existing }
        if ($toAdd) { 
            Add-Content -Path $GitIgnore -Value ($toAdd -join "`n") 
        }
    } else {
        Set-Content -Path $GitIgnore -Value ($giLines -join "`n") -Encoding UTF8
    }
}

# ------------------------------------------------------------
# GitHub Login
# ------------------------------------------------------------
function Login-GitHub {
    [CmdletBinding()]
    param()

    Write-Log "Initiating GitHub CLI login..." 'INFO'

    try {
        Assert-Command 'gh'
    } catch {
        Write-Log "GitHub CLI not found in system PATH." 'ERROR'
        throw "Please install GitHub CLI before proceeding."
    }

    if ($DryRun) {
        Write-Log "Dry-run: Would execute 'gh auth login'" 'INFO'
        return
    }

    try {
        $r = Invoke-SafeCommand 'gh' @('auth','login','--hostname','github.com','--web','--scopes','repo')
        if ($r.Code -ne 0) {
            throw "gh auth login failed: $($r.Stderr.Trim())"
        }
        Write-Log "GitHub CLI login completed successfully." 'INFO'
    } catch {
        Write-Log "GitHub login failed: $($_.Exception.Message)" 'ERROR'
        throw
    }
}

Invoke-Step 'GitHub CLI authentication (optional)' {
    if ($LoginGh) {
        try { 
            Assert-Command 'gh' 
        } catch { 
            throw 'gh not found after install.' 
        }
        $st = Invoke-SafeCommand 'gh' @('auth','status')
        if ($st.Code -ne 0) {
            Write-Log 'gh not authenticated. Launching browser-based login…' 'WARNING'
            Login-GitHub
        } else {
            Write-Log 'gh already authenticated.' 'INFO'
        }
    } else {
        Write-Log 'LoginGh not set; skipping gh auth.' 'DEBUG'
    }
}

# ------------------------------------------------------------
# CLI add-ons: gh-copilot, Claude Code
# ------------------------------------------------------------
function Gh-HasCopilotExtension {
    try {
        $r = Invoke-SafeCommand 'gh' @('extension','list','--json','name,repository')
        if ($r.Code -ne 0) { 
            return $false 
        }
        return ($r.Stdout | ConvertFrom-Json | Where-Object { $_.repository -eq 'github/gh-copilot' }) -ne $null
    } catch { 
        return $false 
    }
}

Invoke-Step 'Install gh-copilot extension' {
    if (-not (Gh-HasCopilotExtension)) {
        Invoke-WithRetry -What 'gh extension install github/gh-copilot' -Action {
            $r = Invoke-SafeCommand 'gh' @('extension','install','github/gh-copilot','-c','stable')
            if ($r.Code -ne 0) { 
                throw "gh extension install failed: $($r.Stderr.Trim())" 
            }
        }
    }
}

Invoke-Step 'Ensure npm -g prefix is on PATH' {
    Assert-Command 'npm'
    $r = Invoke-SafeCommand 'npm' @('config','get','prefix')
    if ($r.Code -eq 0) {
        $prefix = $r.Stdout.Trim()
        if ($prefix -and (Test-Path $prefix)) {
            $bin = Join-Path $prefix 'node_modules\.bin'
            Ensure-Path $bin
        }
    }
}

Invoke-Step 'Install Claude Code (npm global)' {
    try { 
        Assert-Command 'npm' 
    } catch { 
        throw 'Node/npm not found in PATH after install.' 
    }
    $r = Invoke-SafeCommand 'npm' @('list','-g','@anthropic-ai/claude-code')
    if ($r.Stdout -notmatch '@anthropic-ai/claude-code') {
        Invoke-WithRetry -What 'npm install -g @anthropic-ai/claude-code' -Action {
            $r2 = Invoke-SafeCommand 'npm' @('install','-g','@anthropic-ai/claude-code')
            if ($r2.Code -ne 0) { 
                throw "npm install failed: $($r2.Stderr.Trim())" 
            }
        }
    }
}

# ------------------------------------------------------------
# Aliases into user profile (with correct $args forwarding)
# ------------------------------------------------------------
$AliasesContent = @'
# --- AI CLI defaults (loaded by $PROFILE) ---
function aider-auto { param([Parameter(ValueFromRemainingArguments=$true)][object[]]$args) aider --yes-always @args }
function claude-auto { param([Parameter(ValueFromRemainingArguments=$true)][object[]]$args) claude --dangerously-skip-permissions @args }
function codex-auto  { param([Parameter(ValueFromRemainingArguments=$true)][object[]]$args) codex --full-auto @args }
function ghs { param([Parameter(ValueFromRemainingArguments=$true)][object[]]$args) gh copilot suggest @args }
function ghe { param([Parameter(ValueFromRemainingArguments=$true)][object[]]$args) gh copilot explain @args }
'@

Invoke-Step "Write aliases file and add to profile ($PROFILE)" {
    Set-Content -Path $AliasesPs1 -Value $AliasesContent -Encoding UTF8
    if (-not (Test-Path $PROFILE)) { 
        New-Item -ItemType File -Path $PROFILE -Force | Out-Null 
    }
    $prof = Get-Content -Path $PROFILE -ErrorAction SilentlyContinue
    $line = ". '$AliasesPs1'"
    if ($prof -notcontains $line) { 
        Add-Content -Path $PROFILE -Value $line 
    }
}

# ------------------------------------------------------------
# Docker Installation and Compose
# ------------------------------------------------------------
function Install-Docker {
    [CmdletBinding()]
    param()

    Write-Log "Starting Docker installation..." 'INFO'

    try {
        Assert-Command 'docker'
        Write-Log "Docker is already installed." 'INFO'
        return
    } catch {
        Write-Log "Docker not found. Proceeding with installation..." 'WARNING'
    }

    if ($DryRun) {
        Write-Log "Dry-run: Would execute Docker installation command" 'INFO'
        return
    }

    try {
        if (-not (Winget-IsInstalled 'Docker.DockerDesktop')) {
            if ($Admin) { 
                Winget-Install 'Docker.DockerDesktop' 'machine' 
            } else {
                Write-Log 'Docker Desktop requires admin; attempting elevation for Docker-only install…' 'WARNING'
                try {
                    Start-Process -FilePath 'pwsh' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File', $MyInvocation.MyCommand.Path, '-InstallDocker') -Verb RunAs | Out-Null
                    Write-Log 'Elevated child process started for Docker install. Continuing user-scope steps.' 'INFO'
                } catch { 
                    Write-Log 'Elevation failed; skip Docker install.' 'ERROR' 
                }
            }
        }
    } catch {
        Write-Log "Failed to install Docker: $($_.Exception.Message)" 'ERROR'
        throw
    }

    Write-Log "Docker installation completed successfully." 'INFO'
}

function Test-DockerReady {
    try {
        $r = Invoke-SafeCommand 'docker' @('version','--format','{{.Server.Version}}')
        return $r.Code -eq 0 -and ($r.Stdout.Trim().Length -gt 0)
    } catch { 
        return $false 
    }
}

function Start-DockerCompose {
    [CmdletBinding()]
    param()

    if (-not (Test-Path $ComposeYml)) {
        Write-Log "Compose file not found: $ComposeYml" 'ERROR'
        throw "Missing docker-compose.yml"
    }

    if ($DryRun) {
        Write-Log "Dry-run: Would start Docker Compose using $ComposeYml" 'INFO'
        return
    }

    try {
        $r = Invoke-SafeCommand 'docker' @('compose','-f',$ComposeYml,'up','-d')
        if ($r.Code -ne 0) { 
            throw "docker compose up failed: $($r.Stderr.Trim())" 
        }
        Write-Log "Docker Compose started successfully." 'INFO'
    } catch {
        Write-Log "Failed to start Docker Compose: $($_.Exception.Message)" 'ERROR'
        throw
    }
}

Invoke-Step 'Install Docker Desktop (optional)' {
    if ($Config.install.docker) {
        Install-Docker
    }
}

Invoke-Step 'Write Compose v2 stack (Redis + Ollama)' {
    $compose = @"
services:
  redis:
    image: redis:7
    ports: ["6379:6379"]
    restart: unless-stopped
  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes: ["ollama:/root/.ollama"]
    restart: unless-stopped
volumes:
  ollama:
"@
    Set-Content -Path $ComposeYml -Value $compose -Encoding UTF8
}

if (Test-DockerReady) {
    Write-Log "Docker daemon is ready." 'INFO'
    if ($StartCompose) {
        Invoke-Step 'Starting compose stack (-StartCompose)' {
            Start-DockerCompose
        }
    } else {
        Write-Log "Run to start services: docker compose -f `"$ComposeYml`" up -d" 'INFO'
    }
} else {
    Write-Log 'Docker not ready; skipping compose up. Start Docker Desktop and run the compose command later.' 'WARNING'
}

# ------------------------------------------------------------
# Guardrails pre-commit hook
# ------------------------------------------------------------
$PreCommitPath = Join-Path $GuardDir 'pre-commit'
$PreCommitContent = @'
#!/usr/bin/env bash
# Minimal guard: block committing .env and accidental API keys
set -euo pipefail
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  echo "[guardrails] .env is tracked by git. This is unsafe. Untrack it first (git rm --cached .env)." >&2
  exit 1
fi
# very simple grep on staged content (tuned for common key names)
if git diff --cached --name-only | xargs -r git show : | grep -E "(OPENAI_API_KEY|ANTHROPIC_API_KEY|GROQ_API_KEY)=[A-Za-z0-9-_]{10,}" -n >/dev/null 2>&1; then
  echo "[guardrails] Potential API key detected in staged changes. Aborting commit." >&2
  exit 1
fi
exit 0
'@

Invoke-Step 'Install guardrails pre-commit hook' {
    Set-Content -Path $PreCommitPath -Value $PreCommitContent -Encoding UTF8
    if (Test-Path (Join-Path $RepoRoot '.git')) {
        $GitHookDir = Join-Path $RepoRoot '.git\hooks'
        New-Item -ItemType Directory -Force -Path $GitHookDir | Out-Null
        Copy-Item -Path $PreCommitPath -Destination (Join-Path $GitHookDir 'pre-commit') -Force
        try { 
            & bash -lc "chmod +x '$(wslpath -a (Join-Path $GitHookDir 'pre-commit'))'" 
        } catch { 
            Write-Log 'chmod +x failed; hook may not be executable on WSL/Linux.' 'WARNING'
        }
    } else {
        Write-Log 'No .git directory found; hook file written to .ai/guard/pre-commit only.' 'WARNING'
    }
}

# ------------------------------------------------------------
# Quickstart + smoke test
# ------------------------------------------------------------
Invoke-Step 'Write QUICKSTART and test_imports.py' {
    $qs = @(
        '# AI Workstation Quickstart',
        '',
        '## TL;DR',
        '1. Open a new terminal (to load profile aliases).',
        "2. Activate venv: & '$($VenvPath -replace '\\','/')/Scripts/Activate.ps1'",
        '3. (Optional) Start infra: docker compose -f ./.ai/docker/compose.yml up -d (or pass -StartCompose).',
        '4. Run smoke test: python ./.ai/test_imports.py (after venv activation).',
        '',
        '## Environment',
        '- Edit `.env` to add your API keys.',
        '- `.env` and `.ai/logs` are git-ignored.',
        '',
        '## Services',
        '- Redis → `redis://localhost:6379/0`',
        '- Ollama → `http://localhost:11434` (images pulled on first use).',
        '',
        '## Helpful Aliases',
        '- `ghs` → `gh copilot suggest ...`',
        '- `ghe` → `gh copilot explain ...`',
        '- `aider-auto`, `claude-auto`, `codex-auto` to force non-interactive defaults.',
        ''
    ) -join "`n"
    Set-Content -Path $Quickstart -Value $qs -Encoding UTF8

    $py = @(
        'import importlib, sys',
        'pkgs = [',
        '  "pydantic","httpx","tenacity","numpy","pandas","redis",',
        '  "fastapi","uvicorn","typer","yaml","tiktoken","openai","anthropic",',
        '  "langchain","langchain_community","langgraph","duckdb"',
        ']',
        'missing = []',
        'for p in pkgs:',
        '    try: importlib.import_module(p)',
        '    except Exception as e: missing.append((p, repr(e)))',
        'if missing:',
        '    print("Missing/failed:")',
        '    for p,e in missing: print(" ",p, e)',
        '    sys.exit(1)',
        'print("All imports OK")'
    ) -join "`n"
    Set-Content -Path $TestPy -Value $py -Encoding UTF8
}

# ------------------------------------------------------------
# Post-install Doctor
# ------------------------------------------------------------
function Invoke-Doctor {
    Write-Log 'Doctor: verifying tools and imports…' 'INFO'
    
    foreach($cmd in 'git','gh','node','npm',$PyExe,'docker'){
        try { 
            Get-Command $cmd -ErrorAction Stop | Out-Null 
            Write-Log "✓ Command available: $cmd" 'DEBUG'
        } catch { 
            Write-Log "✗ Missing command: $cmd" 'ERROR' 
        }
    }
    
    # gh auth status (only log result)
    try {
        $s = Invoke-SafeCommand 'gh' @('auth','status')
        if ($s.Code -ne 0) { 
            Write-Log 'gh not authenticated.' 'WARNING' 
        } else { 
            Write-Log 'gh authentication OK.' 'INFO' 
        }
    } catch { 
        Write-Log 'gh authentication check failed.' 'WARNING' 
    }
    
    try { 
        & $PyExe $TestPy | ForEach-Object { Write-Log $_ 'INFO' }
    } catch { 
        Write-Log "Python import smoke test failed. See $TestPy." 'ERROR' 
    }
    
    if (Test-DockerReady) {
        $r = Invoke-SafeCommand 'docker' @('ps')
        if ($r.Code -ne 0) { 
            Write-Log "Docker CLI error: $($r.Stderr.Trim())" 'ERROR' 
        } else { 
            Write-Log 'Docker daemon OK.' 'INFO' 
        }
    } else {
        Write-Log 'Docker daemon not ready.' 'WARNING'
    }
}

Invoke-Step 'Post-install doctor' { Invoke-Doctor }

# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------
Write-Log '--- SUMMARY ---' 'INFO'
Write-Log ("Config:       " + (Resolve-Path $ConfigPath).Path) 'INFO'
Write-Log ("Venv:         " + $VenvPath) 'INFO'
Write-Log ("Requirements: " + $ReqPath) 'INFO'
Write-Log (".env:         " + $EnvPath) 'INFO'
Write-Log ("Compose:      " + $ComposeYml) 'INFO'
Write-Log ("Aliases:      " + $AliasesPs1) 'INFO'
Write-Log ("Quickstart:   " + $Quickstart) 'INFO'

Write-Log 'Done. Open a new terminal to load profile changes. Read AI-Setup-QUICKSTART.md for next steps.' 'INFO'