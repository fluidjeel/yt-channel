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

## 2. DevTools header (manual)

Paste Cookie header → `cookies/raw_header.txt` → `python scripts/convert_cookie_header.py`

## 3. Browser extension

Export Netscape format to `cookies/youtube.txt`.

## Deploy only

```powershell
powershell scripts/deploy_cookies_to_oracle.ps1
# or
python scripts/youtube_cookie_sync.py --deploy --restart-batch
```
