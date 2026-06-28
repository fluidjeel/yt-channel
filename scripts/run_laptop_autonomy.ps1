# Laptop autonomy: refresh cookies + poke Oracle orchestrator (safe, no batch restart).
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$LogDir = Join-Path $Root "logs"
$LogFile = Join-Path $LogDir "laptop_autonomy.log"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Key = Join-Path $Root "ssh-key-2026-06-17.key"
$RemoteHost = "ubuntu@80.225.234.65"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "`n=== laptop autonomy $ts ==="

Push-Location $Root
try {
    # Cookies only — corpus iteration paused after batch 3 (no orchestrator ticks).
    if (Test-Path $Python) {
        & $Python (Join-Path $Root "scripts\youtube_cookie_sync.py") --deploy --smoke --login-timeout 90 2>&1 |
            Tee-Object -FilePath $LogFile -Append
    }
} finally {
    Pop-Location
}
