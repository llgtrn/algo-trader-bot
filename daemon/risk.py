"""Risk guardrails — built BEFORE any order code (blueprint §5).

Phase 1 wires the *gates* (kill switch, demo/live gate, cap predicate) but not
execution. ``reconcile`` is a deliberate stub: the daemon must never place an
order until Phase 3 implements it under these rails.
"""

from __future__ import annotations

from pathlib import Path

from .config import Settings


def is_halted(settings: Settings) -> bool:
    """True when the kill switch is engaged.

    The sentinel file is the always-available kill switch: ``touch ./HALT``
    stops new orders. (Telegram ``/halt`` is added alongside it in a later
    phase; both routes set this same state.)
    """
    return Path(settings.kill_switch_file).exists()


def demo_gate(settings: Settings) -> None:
    """Refuse to run against a live account unless explicitly confirmed.

    Raises ``RuntimeError`` if ``HOST=live`` without ``LIVE_CONFIRMED=1``. Demo
    is always allowed. Call this before any code path that could trade.
    """
    if settings.is_live and not settings.live_confirmed:
        raise RuntimeError(
            "HOST=live but LIVE_CONFIRMED is not set. Live trading is gated; "
            "set LIVE_CONFIRMED=1 to acknowledge after demo soak-testing."
        )


def within_caps(settings: Settings, snapshot: dict) -> tuple[bool, str]:
    """Check a snapshot against the configured caps.

    Returns ``(ok, reason)``. ``ok`` is False if any cap is breached; ``reason``
    explains which. Caps of 0 mean "unset → not enforced" in this phase.
    """
    positions = snapshot.get("positions", [])

    if settings.max_positions and len(positions) > settings.max_positions:
        return False, (
            f"max_positions breached: {len(positions)} > {settings.max_positions}"
        )

    if settings.max_lots:
        total_lots = sum(abs(p.get("volume", 0.0)) for p in positions)
        if total_lots > settings.max_lots:
            return False, f"max_lots breached: {total_lots} > {settings.max_lots}"

    if settings.max_daily_loss:
        net_pnl = snapshot.get("net_pnl", 0.0) or 0.0
        if net_pnl <= -abs(settings.max_daily_loss):
            return False, (
                f"max_daily_loss breached: net_pnl {net_pnl} <= "
                f"-{abs(settings.max_daily_loss)}"
            )

    return True, "ok"


def reconcile(*args, **kwargs):  # pragma: no cover - intentionally unimplemented
    """Stance→order reconciliation. NOT implemented in Phase 1 (snapshot-only).

    Phase 3 implements: stance says enter + no position + within rails ⇒ place
    order (demo first); price hit invalidation ⇒ close; stance flipped ⇒
    flatten/reverse. Until then the daemon never places orders.
    """
    raise NotImplementedError("Order reconciliation arrives in Phase 3.")
