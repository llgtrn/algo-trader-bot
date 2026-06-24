"""The 24/7 heartbeat loop — Phase 1, snapshot-only (NO trading).

Per tick: connect (once) → live snapshot → read latest stance per instrument →
append an audit row → post a Telegram heartbeat → sleep. It honours the kill
switch and the demo/live gate, but it never places an order in this phase.

Run with: ``python -m daemon.heartbeat``
"""

from __future__ import annotations

import signal
import sys
import time
from datetime import datetime, timedelta, timezone

from . import risk, state, stance_store, telegram
from .config import Settings, load_settings
from .ctrader_client import CTraderClient

_running = True


def _handle_sigint(signum, frame):  # noqa: ARG001
    global _running
    _running = False
    print("\nShutting down heartbeat...", file=sys.stderr)


def _read_stances(settings: Settings) -> dict:
    """instrument → Stance|None (None = flat/stale/missing)."""
    return {
        instrument: stance_store.read_latest(settings.stance_db_path, instrument)
        for instrument in settings.watchlist
    }


def tick(settings: Settings, client: CTraderClient) -> None:
    """One heartbeat iteration."""
    halted = risk.is_halted(settings)
    snapshot = client.snapshot()
    stances = _read_stances(settings)

    eta = (
        datetime.now(timezone.utc) + timedelta(seconds=settings.heartbeat_seconds)
    ).strftime("%H:%M:%SZ")
    last_action = "halted (kill switch)" if halted else "none (snapshot-only)"

    # Audit row — informational in this phase.
    state.append_decision(
        settings.stance_db_path,
        kind="heartbeat",
        payload={
            "halted": halted,
            "error": snapshot.get("error"),
            "positions_count": len(snapshot.get("positions", [])),
            "net_pnl": snapshot.get("net_pnl"),
            "stances": {
                k: (v.direction if v else "flat") for k, v in stances.items()
            },
        },
    )

    message = telegram.format_heartbeat(
        snapshot, stances, next_analysis_eta=eta, last_action=last_action
    )
    sent = telegram.send_message(settings, message)
    print(message + (f"\n[telegram sent={sent}]\n" if True else ""))


def main() -> int:
    signal.signal(signal.SIGINT, _handle_sigint)
    signal.signal(signal.SIGTERM, _handle_sigint)

    settings = load_settings()
    risk.demo_gate(settings)  # refuse live without explicit confirmation
    stance_store.init_db(settings.stance_db_path)
    state.init_db(settings.stance_db_path)

    print(
        f"Starting heartbeat: host={settings.host} "
        f"watchlist={settings.watchlist} cadence={settings.heartbeat_seconds}s"
    )

    client = CTraderClient()
    if not client.connect():
        # Surface a clear failure but keep reporting flats so the operator sees
        # the daemon is alive and that cTrader is unreachable.
        reason = client.last_error or "unknown"
        telegram.send_message(
            settings, f"⚠️ algo-trader-bot: cTrader connect failed — {reason}"
        )
        print(f"cTrader connection failed: {reason}", file=sys.stderr)

    try:
        while _running:
            try:
                tick(settings, client)
            except Exception as exc:  # noqa: BLE001 - one bad tick must not kill loop
                print(f"tick error: {exc}", file=sys.stderr)
            # Sleep in small slices so SIGINT is responsive.
            slept = 0
            while _running and slept < settings.heartbeat_seconds:
                time.sleep(1)
                slept += 1
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
