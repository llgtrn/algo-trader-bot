"""Daemon configuration, loaded from environment / .env.

Single ``load_settings()`` entry point returns an immutable ``Settings``
snapshot. Everything the daemon needs (cadence, watchlist, risk caps, bus
location, Telegram + cTrader credentials) is read here so the rest of the
package never touches ``os.environ`` directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is a declared dependency
    load_dotenv = None


def _csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip().upper() for item in value.split(",") if item.strip()]


def _float(value: str | None, default: float) -> float:
    try:
        return float(value) if value not in (None, "") else default
    except ValueError:
        return default


def _int(value: str | None, default: int) -> int:
    try:
        return int(value) if value not in (None, "") else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    # cTrader execution venue
    host: str = "demo"  # "demo" | "live"
    live_confirmed: bool = False  # explicit opt-in required before HOST=live trades

    # Heartbeat cadence + universe
    heartbeat_seconds: int = 300
    watchlist: list[str] = field(default_factory=list)

    # Risk caps (consumed by risk.py; execution itself is Phase 3)
    max_lots: float = 0.0
    max_positions: int = 0
    max_daily_loss: float = 0.0
    kill_switch_file: str = "./HALT"

    # Stance bus
    stance_store: str = "sqlite"
    stance_db_path: str = "./algo-trader-bot.db"

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    @property
    def is_live(self) -> bool:
        return self.host.lower() == "live"

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)


def load_settings(env_file: str | None = None) -> Settings:
    """Read environment (optionally loading an .env first) into a Settings."""
    if load_dotenv is not None:
        # Load the given file, else a repo-root .env if present.
        if env_file:
            load_dotenv(env_file)
        else:
            root_env = Path(__file__).resolve().parent.parent / ".env"
            load_dotenv(root_env if root_env.exists() else None)

    return Settings(
        host=os.getenv("HOST", "demo").lower(),
        live_confirmed=os.getenv("LIVE_CONFIRMED", "").lower() in {"1", "true", "yes"},
        heartbeat_seconds=_int(os.getenv("HEARTBEAT_SECONDS"), 300),
        watchlist=_csv(os.getenv("WATCHLIST")),
        max_lots=_float(os.getenv("MAX_LOTS"), 0.0),
        max_positions=_int(os.getenv("MAX_POSITIONS"), 0),
        max_daily_loss=_float(os.getenv("MAX_DAILY_LOSS"), 0.0),
        kill_switch_file=os.getenv("KILL_SWITCH_FILE", "./HALT"),
        stance_store=os.getenv("STANCE_STORE", "sqlite").lower(),
        stance_db_path=os.getenv("STANCE_DB_PATH", "./algo-trader-bot.db"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
    )
