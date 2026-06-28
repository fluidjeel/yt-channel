#!/usr/bin/env python3
"""
Capture YouTube cookies via Playwright and optionally deploy to Oracle VM.

First run (login once):
  pip install -r requirements-cookies.txt
  playwright install chromium
  python scripts/youtube_cookie_sync.py --headed

Refresh + deploy to Oracle:
  python scripts/youtube_cookie_sync.py --deploy --restart-batch

Uses persistent profile at cookies/browser_profile/ (gitignored).
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.cookie_netscape import has_youtube_session, write_netscape

logger = logging.getLogger(__name__)

DEFAULT_COOKIE_OUT = PROJECT_ROOT / "cookies" / "youtube.txt"
DEFAULT_PROFILE = PROJECT_ROOT / "cookies" / "browser_profile"
DEFAULT_ORACLE_HOST = "ubuntu@80.225.234.65"
DEFAULT_ORACLE_KEY = PROJECT_ROOT / "ssh-key-2026-06-17.key"
SMOKE_URL = "https://www.youtube.com/shorts/ab3Zy4c32lw"


def _profile_exists(profile_dir: Path) -> bool:
    if not profile_dir.exists():
        return False
    return any(profile_dir.iterdir())


def _capture_cookies(
    profile_dir: Path,
    *,
    headed: bool,
    login_timeout_sec: int,
) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit(
            "Playwright not installed. Run:\n"
            "  pip install -r requirements-cookies.txt\n"
            "  playwright install chromium"
        ) from exc

    profile_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=not headed,
            locale="en-US",
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        logger.info("Opening YouTube (profile: %s)", profile_dir)
        page.goto("https://www.youtube.com", wait_until="domcontentloaded", timeout=120_000)

        deadline = time.monotonic() + login_timeout_sec
        while time.monotonic() < deadline:
            cookies = context.cookies()
            if has_youtube_session(cookies):
                logger.info("YouTube session detected (%d cookies)", len(cookies))
                break
            if headed:
                logger.info(
                    "Log in to YouTube in the browser window (%ds left)...",
                    int(deadline - time.monotonic()),
                )
            time.sleep(3)
        else:
            context.close()
            raise RuntimeError(
                "No YouTube session cookies after timeout. Re-run with --headed and sign in."
            )

        # Refresh cookies after any post-login navigation
        page.goto("https://www.youtube.com/feed/subscriptions", wait_until="domcontentloaded", timeout=60_000)
        time.sleep(2)
        cookies = context.cookies()
        context.close()
        return cookies


def _local_smoke(cookie_path: Path) -> bool:
    import shutil

    ytdlp = shutil.which("yt-dlp")
    if not ytdlp:
        venv = PROJECT_ROOT / ".venv" / "Scripts" / "yt-dlp.exe"
        if venv.exists():
            ytdlp = str(venv)
        else:
            logger.warning("yt-dlp not found — skipping local smoke test")
            return True
    r = subprocess.run(
        [ytdlp, "--cookies", str(cookie_path), "-F", SMOKE_URL],
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = (r.stdout or "") + (r.stderr or "")
    ok = "mp4" in out.lower() or "webm" in out.lower() or "m4a" in out.lower()
    if not ok:
        logger.warning("Local smoke test weak/failed (Oracle IP may still differ):\n%s", out[-500:])
    return ok


def deploy_to_oracle(
    cookie_path: Path,
    *,
    host: str,
    key_path: Path,
    smoke: bool,
    restart_batch: bool,
) -> None:
    if not key_path.exists():
        raise FileNotFoundError(f"SSH key not found: {key_path}")
    remote = f"{host}:~/yt-channel/cookies/youtube.txt"
    subprocess.run(
        ["scp", "-i", str(key_path), str(cookie_path), remote],
        check=True,
        timeout=60,
    )
    logger.info("SCP complete → %s", remote)

    smoke_cmd = ""
    if smoke:
        smoke_cmd = (
            "export PATH=$HOME/.deno/bin:$PATH && source .venv/bin/activate && "
            f"yt-dlp --cookies cookies/youtube.txt -F '{SMOKE_URL}' 2>&1 | head -12; "
        )

    restart_cmd = ""
    if restart_batch:
        restart_cmd = (
            "tmux kill-session -t corpus-batch 2>/dev/null || true; "
            "tmux new-session -d -s corpus-batch 'bash scripts/start_batch_tmux.sh'; "
        )

    remote_script = (
        f"chmod 600 ~/yt-channel/cookies/youtube.txt && cd ~/yt-channel && "
        f"{smoke_cmd}{restart_cmd}tmux ls 2>/dev/null || true"
    )
    subprocess.run(
        ["ssh", "-i", str(key_path), "-o", "ConnectTimeout=25", host, remote_script],
        check=True,
        timeout=180,
    )
    logger.info("Oracle deploy complete (restart_batch=%s)", restart_batch)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync YouTube cookies to yt-dlp / Oracle VM")
    parser.add_argument("--out", type=Path, default=DEFAULT_COOKIE_OUT)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--headed", action="store_true", help="Show browser (required for first login)")
    parser.add_argument("--login-timeout", type=int, default=300, help="Seconds to wait for login")
    parser.add_argument("--deploy", action="store_true", help="SCP cookies to Oracle VM")
    parser.add_argument("--host", default=DEFAULT_ORACLE_HOST)
    parser.add_argument("--key", type=Path, default=DEFAULT_ORACLE_KEY)
    parser.add_argument(
        "--deploy-only",
        action="store_true",
        help="Skip browser; deploy existing --out file to Oracle",
    )
    parser.add_argument("--smoke", action="store_true", help="Run yt-dlp format check locally + on VM")
    parser.add_argument(
        "--restart-batch",
        action="store_true",
        help="Restart corpus-batch tmux on Oracle after deploy",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if args.deploy_only:
        if not args.out.exists():
            logger.error("Missing %s — run without --deploy-only first", args.out)
            return 1
        if args.smoke:
            _local_smoke(args.out)
        deploy_to_oracle(
            args.out,
            host=args.host,
            key_path=args.key,
            smoke=args.smoke,
            restart_batch=args.restart_batch,
        )
        return 0

    headed = args.headed
    if not headed and not _profile_exists(args.profile):
        logger.info("No browser profile yet — forcing --headed for first login")
        headed = True

    cookies = _capture_cookies(
        args.profile,
        headed=headed,
        login_timeout_sec=args.login_timeout,
    )
    count = write_netscape(args.out, cookies)
    logger.info("Wrote %s (%d YouTube cookies)", args.out, count)

    if not has_youtube_session(cookies):
        logger.error("Export missing session cookies (SID/PSID/LOGIN_INFO)")
        return 1

    if args.smoke:
        _local_smoke(args.out)

    if args.deploy:
        deploy_to_oracle(
            args.out,
            host=args.host,
            key_path=args.key,
            smoke=args.smoke,
            restart_batch=args.restart_batch,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
