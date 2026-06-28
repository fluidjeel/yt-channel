# Scheduled cookie refresh: headless Playwright profile → Oracle SCP (no batch restart).
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$LogDir = Join-Path $Root "logs"
$LogFile = Join-Path $LogDir "cookie_sync.log"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\youtube_cookie_sync.py"

if (-not (Test-Path $Python)) {
    Write-Error "Missing venv python at $Python"
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "`n=== cookie sync $ts ==="

Push-Location $Root
try {
    & $Python $Script --deploy --smoke --login-timeout 90 2>&1 | Tee-Object -FilePath $LogFile -Append
    if ($LASTEXITCODE -ne 0) {
        Add-Content -Path $LogFile -Value "EXIT CODE: $LASTEXITCODE (session may need --headed login)"
        exit $LASTEXITCODE
    }
} finally {
    Pop-Location
}
