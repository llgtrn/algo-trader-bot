"""Decision → Stance mapping and emission (single source of truth).

The brain produces a TradingAgents decision; this module turns it into the
``Stance`` the daemon consumes and writes it to the bus. The pure mapping
functions here are unit-tested without any LLM call.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Reach the daemon's stance_store (repo root on path).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from daemon.stance_store import Stance, write_stance  # noqa: E402

# Map the TradingAgents 5-tier rating → (direction, conviction).
# Buy/Overweight ⇒ long, Sell/Underweight ⇒ short, Hold ⇒ flat.
_RATING_MAP: dict[str, tuple[str, float]] = {
    "buy": ("long", 0.8),
    "overweight": ("long", 0.6),
    "hold": ("flat", 0.0),
    "underweight": ("short", 0.6),
    "sell": ("short", 0.8),
}


def rating_to_direction_conviction(rating: str) -> tuple[str, float]:
    """Pure mapping. Unknown/blank ratings are treated as flat (safe default)."""
    return _RATING_MAP.get((rating or "").strip().lower(), ("flat", 0.0))


def parse_float_field(markdown: str | None, label: str) -> float | None:
    """Pull a ``**Label**: 1.2345`` numeric value out of a rendered report."""
    if not markdown:
        return None
    match = re.search(
        rf"\*\*{re.escape(label)}\*\*:\s*([-+]?\d+(?:\.\d+)?)", markdown
    )
    return float(match.group(1)) if match else None


def first_sentence(text: str | None, limit: int = 240) -> str:
    if not text:
        return ""
    text = text.strip().replace("\n", " ")
    return text[:limit]


def build_stance(
    instrument: str,
    rating: str,
    final_state: dict | None = None,
    *,
    ttl_minutes: int = 240,
    now: datetime | None = None,
) -> Stance:
    """Assemble a Stance from a rating + the graph's final_state.

    - direction/conviction ← rating
    - target ← Portfolio Manager "Price Target"
    - invalidation ← Trader "Stop Loss" (TODO: derive a heuristic stop when the
      trader omits one — until then it's None and the daemon won't auto-stop)
    - rationale ← final decision summary
    """
    final_state = final_state or {}
    direction, conviction = rating_to_direction_conviction(rating)

    pm_md = final_state.get("final_trade_decision", "")
    trader_md = final_state.get("trader_investment_plan", "")

    target = parse_float_field(pm_md, "Price Target")
    invalidation = parse_float_field(trader_md, "Stop Loss")
    rationale = first_sentence(pm_md) or f"Rating: {rating}"

    return Stance(
        instrument=instrument.upper(),
        direction=direction,
        conviction=conviction,
        entry_zone=None,  # market entry; entry_zone refinement is later work
        invalidation=invalidation,
        target=target,
        rationale=rationale,
        issued_at=now or datetime.now(timezone.utc),
        ttl_minutes=ttl_minutes,
    )


def emit_stance(db_path: str, stance: Stance) -> None:
    """Persist a stance to the bus."""
    write_stance(db_path, stance)
