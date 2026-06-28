# Unattended operation (6+ hours)

## Laptop (must stay awake — sleep/hibernate pauses tasks; screen lock OK)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_autonomy_task.ps1
```

Every **30 min** (`YT-Channel-Autonomy`):

1. Headless Playwright cookie sync → Oracle SCP
2. SSH: one safe `autonomy_orchestrator.py` tick (retry 1 download or 1 analyze)

Logs: `logs/laptop_autonomy.log`, `logs/cookie_sync.log`

## Oracle VM

```bash
tmux new-session -d -s oracle-autonomy 'bash scripts/oracle_autonomy_watchdog.sh'
```

Every **15 min** on VM:

- Resource guard (disk/mem/load) — skips work if unsafe
- Never starts work if `corpus-batch` tmux already running
- One channel download or analyze per tick

Status: `data/autonomy/status.json`, `reports/corpus_health.md`

## Hard limits (won't crash VM)

| Guard | Limit |
|-------|--------|
| Disk used | pause if ≥ 85% |
| Memory used | pause if ≥ 88% |
| Load (1m) | pause if ≥ 3.5 |
| Per tick | 1 channel only |
| Video | ≤ 180s, ≤ 500 MB |
| Batch | ≤ 25 GB |

## Cannot automate

- Google re-login / 2FA / captcha (`--headed` once when back)
