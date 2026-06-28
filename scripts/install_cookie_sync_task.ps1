# Register Windows Scheduled Task: refresh YouTube cookies every 30 minutes.
param(
    [int]$IntervalMinutes = 30,
    [switch]$Unregister
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$TaskName = "YT-Channel-CookieSync"
$Runner = Join-Path $Root "scripts\run_cookie_sync_scheduled.ps1"

if ($Unregister) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Removed scheduled task: $TaskName"
    exit 0
}

if (-not (Test-Path $Runner)) {
    Write-Error "Missing $Runner"
}

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Runner`"" `
    -WorkingDirectory $Root

$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null

Write-Host "Registered: $TaskName"
Write-Host "  Every: $IntervalMinutes minutes"
Write-Host "  Script: $Runner"
Write-Host "  Log:    $Root\logs\cookie_sync.log"
Write-Host ""
Write-Host "Test now: powershell -File `"$Runner`""
Write-Host "Remove:   powershell -File `"$PSCommandPath`" -Unregister"
