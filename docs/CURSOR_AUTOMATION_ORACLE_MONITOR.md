# Cursor Automation — Oracle Corpus Monitor (every 30 min)

Use this doc to create a **Cursor Automation** that checks Phase 1 corpus sprint progress on Oracle.

> **Editor handoff:** In Cursor, open **Automations** (Agents window) → **New automation** → paste settings below.  
> This chat session cannot open the Automations editor directly; use the Agents window or create manually.

---

## Draft summary

| Field | Value |
|-------|--------|
| **Name** | Oracle corpus sprint monitor |
| **Description** | Every 30 minutes, SSH to Oracle VM and report Phase 1 corpus progress (tmux, profiles, cookie errors). Read-only unless sprint died. |
| **Trigger** | Schedule — every **30 minutes** (`*/30 * * * *`) |
| **Repo** | `fluidjeel/yt-channel` · branch `main` |
| **Runtime** | Cloud agent (needs outbound SSH + secret for private key) |
| **Tools** | Shell / terminal only (no Slack, no MCP required) |

### To finish in Automations editor

1. Add **secret**: `ORACLE_SSH_PRIVATE_KEY` — contents of your `ssh-key-2026-06-17.key` (never commit the key).
2. Confirm **cloud agent** can reach `80.225.234.65:22`.
3. Enable schedule timezone if the UI offers it (cron is UTC unless configured).
4. Save and enable the automation.

---

## Agent instructions (paste into Automation prompt)

```
You monitor the YouTube channel corpus sprint on an Oracle VM. Read-only checks only — do not restart tmux or change the queue unless the action field says tmux died.

## Setup (each run)
1. Checkout repo fluidjeel/yt-channel branch main.
2. Write the secret ORACLE_SSH_PRIVATE_KEY to a temp file, chmod 600.
3. SSH host: ubuntu@80.225.234.65

## Remote commands (single SSH session)
ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 -i <keyfile> ubuntu@80.225.234.65 << 'REMOTE'
cd ~/yt-channel
source .venv/bin/activate 2>/dev/null || true
echo "=== TMUX ==="
tmux has-session -t corpus 2>/dev/null && echo "corpus: running" || echo "corpus: stopped"
echo "=== PROFILES ==="
ls reports/*/mvp_profile.json 2>/dev/null | wc -l
echo "=== PHASE1 QUEUE ==="
grep -c "url:" corpus_queue_phase1.yaml 2>/dev/null || echo 0
echo "=== RUN LOG ==="
wc -l data/corpus/run_log.jsonl 2>/dev/null || echo 0
tail -1 data/corpus/run_log.jsonl 2>/dev/null
echo "=== BOT ERRORS (log tail) ==="
tail -30 ~/logs/corpus_sprint.log 2>/dev/null | grep -ci "not a bot" || echo 0
echo "=== TMUX TAIL ==="
tmux capture-pane -t corpus -p 2>/dev/null | tail -8
REMOTE

## Report format (concise)
- Phase: pilot 10% (5 channels)
- Progress: X/5 logged runs, Y mvp profiles
- tmux corpus: running | stopped
- Last slug + status from run_log tail
- Bot errors in recent log: count (if >= 2 → "cookies may be stale — user should refresh")
- Recommended action: ok_running | refresh_cookies | restart_tmux | phase1_complete_run_analyze_corpus

Do not paste private keys. Do not modify the VM unless tmux is stopped and queue incomplete — then say "recommend: restart scripts/start_corpus_tmux.sh" without running it unless user configured auto-remediation.

If SSH fails, report connection error only.
```

---

## Schedule (cron)

```text
*/30 * * * *
```

Every 30 minutes, UTC (adjust in UI if your timezone picker is available).

---

## After Phase 1 completes

Update the automation prompt queue file reference from `corpus_queue_phase1.yaml` to `corpus_queue_phase2.yaml`, or disable the automation until Phase 2 starts.

Run on VM once manually to validate:

```bash
python scripts/corpus_monitor.py
```

(Also committed — optional local/VM helper; the Automation uses SSH directly.)

---

## Security

- Rotate YouTube/Google cookies if exposed; SSH key should only live in Automation secrets.
- Automation is **monitor-only** by default.
