# YouTube cookies (HITL — one-time setup)

Oracle VM IPs often trigger YouTube bot checks. Export cookies once:

1. Install **Get cookies.txt LOCALLY** (Chrome) or use `yt-dlp --cookies-from-browser chrome`
2. Save as `cookies/youtube.txt` (Netscape format)
3. Copy to VM:

```powershell
scp -i .\ssh-key-2026-06-17.key .\cookies\youtube.txt ubuntu@80.225.234.65:~/yt-channel/cookies/youtube.txt
```

4. Restart corpus sprint (or let next channel pick up cookies after pull)

Also set locally for Windows runs: same file path `cookies/youtube.txt`.
