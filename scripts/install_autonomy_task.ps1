# Register laptop autonomy: cookies + Oracle orchestrator every 30 minutes.
param(
    [int]$IntervalMinutes = 30,
    [switch]$Unregister
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$TaskName = "YT-Channel-Autonomy"
$Runner = Join-Path $Root "scripts\run_laptop_autonomy.ps1"

# Keep legacy cookie-only task name in sync — replace with unified autonomy task
$LegacyName = "YT-Channel-CookieSync"
Unregister-ScheduledTask -TaskName $LegacyName -Confirm:$false -ErrorAction SilentlyContinue

if ($Unregister) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Removed scheduled task: $TaskName"
    exit 0
}

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Runner`"" `
    -WorkingDirectory $Root

$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null

Write-Host "Registered: $TaskName (every $IntervalMinutes min)"
Write-Host "  Cookies + Oracle orchestrator"
Write-Host "  Log: $Root\logs\laptop_autonomy.log"
Write-Host "  Requires: PC awake (no sleep/hibernate); screen lock OK"
