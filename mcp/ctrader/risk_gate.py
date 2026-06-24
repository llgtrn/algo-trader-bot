"""Hard risk gate for the cTrader MCP server.

When Claude Code trades directly through the MCP tools, the daemon's risk.py is
NOT in the path — so the rails must live here, enforced in code, not in Claude's
good behavior. Every order tool runs through ``check_order`` before anything is
sent to the broker; a violation returns a structured rejection and the order is
never placed.

Config comes from the same environment the bot uses (so it works whether the MCP
is launched standalone or by Claude Code):

    HOST=demo|live              # live requires LIVE_CONFIRMED=1
    LIVE_CONFIRMED=1            # explicit acknowledgement for live trading
    KILL_SWITCH_FILE=./HALT     # presence ⇒ all new orders rejected
    MAX_ORDER_LOTS=0.10         # per-order volume cap (0/unset ⇒ not enforced)
    MAX_POSITIONS=5             # max concurrent open positions (0/unset ⇒ off)
    REQUIRE_STOP_LOSS=1         # reject entry orders without a stop_loss
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GateResult:
    allowed: bool
    reason: str = "ok"

    def as_dict(self) -> dict:
        return {"allowed": self.allowed, "reason": self.reason}


def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _float(name: str, default: float = 0.0) -> float:
    try:
        return float(os.getenv(name, "") or default)
    except ValueError:
        return default


def _int(name: str, default: int = 0) -> int:
    try:
        return int(os.getenv(name, "") or default)
    except ValueError:
        return default


def is_killed() -> bool:
    """Kill switch: sentinel file present ⇒ stop all new orders."""
    return Path(os.getenv("KILL_SWITCH_FILE", "./HALT")).exists()


def live_gate() -> GateResult:
    """Block live trading unless explicitly confirmed."""
    host = os.getenv("HOST", "demo").strip().lower()
    if host == "live" and not _flag("LIVE_CONFIRMED"):
        return GateResult(
            False,
            "HOST=live but LIVE_CONFIRMED is not set — live trading is gated. "
            "Set LIVE_CONFIRMED=1 to acknowledge after demo soak-testing.",
        )
    return GateResult(True)


def check_order(
    *,
    is_entry: bool,
    volume: float | None = None,
    stop_loss: float | None = None,
    open_positions: int = 0,
) -> GateResult:
    """Gate a single order. Returns GateResult(allowed=False, reason=...) on any breach.

    ``is_entry`` distinguishes opening orders (market/limit/stop entries) from
    risk-reducing actions (close/cancel), which are always allowed through even
    when the kill switch is on.
    """
    # Risk-reducing actions (close/cancel) are always allowed — never trap a
    # user who needs to flatten, even with the kill switch on or live unconfirmed.
    if not is_entry:
        return GateResult(True)

    if is_killed():
        return GateResult(False, "kill switch engaged (sentinel file present) — new orders rejected")

    gate = live_gate()
    if not gate.allowed:
        return gate

    if _flag_default("REQUIRE_STOP_LOSS", True) and (stop_loss is None):
        return GateResult(False, "stop_loss is mandatory for entry orders (REQUIRE_STOP_LOSS)")

    max_lots = _float("MAX_ORDER_LOTS")
    if max_lots and volume is not None and volume > max_lots:
        return GateResult(False, f"order volume {volume} exceeds MAX_ORDER_LOTS {max_lots}")

    max_positions = _int("MAX_POSITIONS")
    if max_positions and open_positions >= max_positions:
        return GateResult(
            False,
            f"open positions {open_positions} at/over MAX_POSITIONS {max_positions}",
        )

    return GateResult(True)


def _flag_default(name: str, default: bool) -> bool:
    """Like _flag but defaults to True when the var is unset (safety-on default)."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
