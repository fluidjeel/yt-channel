# Deploy cookies/youtube.txt to Oracle VM (wrapper).
param(
    [string]$Key = "ssh-key-2026-06-17.key",
    [string]$Host = "ubuntu@80.225.234.65",
    [switch]$RestartBatch
)

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Args = @("scripts/youtube_cookie_sync.py", "--deploy-only", "--smoke")
if ($RestartBatch) { $Args += "--restart-batch" }

Push-Location $Root
try {
    & python @Args --key (Join-Path $Root $Key) --host $Host
} finally {
    Pop-Location
}
