# YouTube cookies

Oracle VM IPs trigger YouTube bot checks. Three ways to refresh `cookies/youtube.txt` (gitignored):

## 1. Playwright sync (recommended)

```powershell
pip install -r requirements-cookies.txt
playwright install chromium

# First time: sign in when the browser opens
python scripts/youtube_cookie_sync.py --headed --deploy --smoke --restart-batch

# Later: headless refresh + deploy
python scripts/youtube_cookie_sync.py --deploy --restart-batch
```

Persistent login profile: `cookies/browser_profile/` (never commit).

### Windows: every 30 minutes (unattended)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_cookie_sync_task.ps1
powershell -File scripts/run_cookie_sync_scheduled.ps1   # test once
# Log: logs/cookie_sync.log
powershell -File scripts/install_cookie_sync_task.ps1 -Unregister
```

Refreshes cookies on Oracle only (does **not** restart corpus-batch each run).


Paste Cookie header → `cookies/raw_header.txt` → `python scripts/convert_cookie_header.py`

## 3. Browser extension

Export Netscape format to `cookies/youtube.txt`.

## Deploy only

```powershell
powershell scripts/deploy_cookies_to_oracle.ps1
# or
python scripts/youtube_cookie_sync.py --deploy --restart-batch
```
