#!/usr/bin/env python3
"""Manually refresh the cTrader access token and persist it to .env.

Use this to force a refresh (e.g. monthly, or via cron / a scheduled Routine):

    python scripts/refresh_token.py

Reads CLIENT_ID / CLIENT_SECRET / REFRESH_TOKEN from the repo-root .env (or the
current environment), exchanges the refresh token for a fresh pair, and writes
ACCESS_TOKEN / REFRESH_TOKEN / ACCESS_TOKEN_EXPIRES_AT back to .env. The refresh
token rotates, so always let this update the file.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "mcp" / "ctrader"))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from token_refresh import ensure_fresh  # noqa: E402


def main() -> int:
    env_path = _REPO_ROOT / ".env"
    if load_dotenv is not None and env_path.exists():
        load_dotenv(env_path)

    token = ensure_fresh(env_path=str(env_path), force=True)
    if token:
        print(f"OK — access token refreshed and saved to {env_path}")
        return 0
    print("Refresh did not complete — check CLIENT_ID/CLIENT_SECRET/REFRESH_TOKEN.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
