"""Telegram reporting — send-only for Phase 1.

Posts the 5-min heartbeat and alerts. Inbound command polling (``/halt`` etc.)
is deferred; the kill switch in this phase is the sentinel file (see risk.py).
"""

from __future__ import annotations

from datetime import datetime, timezone

try:
    import requests
except ImportError:  # pragma: no cover - requests is a declared dependency
    requests = None

from .config import Settings

_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_message(settings: Settings, text: str) -> bool:
    """Send a message to the configured chat. Returns True on success.

    Silently no-ops (returns False) when Telegram is not configured, so the
    daemon keeps running even without a bot token.
    """
    if not settings.telegram_enabled or requests is None:
        return False
    try:
        resp = requests.post(
            _API.format(token=settings.telegram_bot_token),
            json={
                "chat_id": settings.telegram_chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
        return resp.ok
    except Exception:  # network hiccup must not kill the heartbeat
        return False


def _fmt_money(value) -> str:
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "—"


def format_heartbeat(
    snapshot: dict,
    stances: dict,
    next_analysis_eta: str | None = None,
    last_action: str = "none (snapshot-only)",
) -> str:
    """Render the heartbeat message from a snapshot + per-instrument stances.

    ``snapshot`` is the dict from ctrader_client.snapshot(); ``stances`` maps
    instrument → Stance|None (None = flat/stale).
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    lines = [f"*algo-trader-bot heartbeat* — {now}"]

    if snapshot.get("error"):
        lines.append(f"⚠️ snapshot error: {snapshot['error']}")
        return "\n".join(lines)

    equity = snapshot.get("equity")
    balance = snapshot.get("balance")
    margin = snapshot.get("margin")
    net_pnl = snapshot.get("net_pnl")

    lines.append(
        f"equity `{_fmt_money(equity)}` | balance `{_fmt_money(balance)}` | "
        f"margin `{_fmt_money(margin)}` | open P&L `{_fmt_money(net_pnl)}`"
    )

    positions = snapshot.get("positions", [])
    if positions:
        lines.append(f"*positions ({len(positions)})*:")
        for p in positions:
            lines.append(
                f"  • {p.get('symbol', p.get('symbol_id'))} {p.get('side')} "
                f"{p.get('volume')} lots @ {p.get('entry_price')} "
                f"(P&L {_fmt_money(p.get('pnl'))})"
            )
    else:
        lines.append("*positions*: flat")

    if stances:
        lines.append("*stances*:")
        for instrument, stance in stances.items():
            if stance is None:
                lines.append(f"  • {instrument}: flat (no/stale stance)")
            else:
                lines.append(
                    f"  • {instrument}: {stance.direction} "
                    f"(conv {stance.conviction:.2f}) — {stance.rationale[:80]}"
                )

    lines.append(f"last action: {last_action}")
    if next_analysis_eta:
        lines.append(f"next analysis ETA: {next_analysis_eta}")
    return "\n".join(lines)
