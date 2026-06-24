"""Integration test for one heartbeat tick, with a fake cTrader client.

Exercises the full snapshot → read-stances → audit → render path without a
reactor, credentials, or Telegram. A lightweight FakeClient returns a canned
snapshot so the tick is fast and deterministic.
"""

from datetime import datetime, timezone

from daemon import heartbeat, state, stance_store
from daemon.config import Settings
from daemon.stance_store import Stance


class FakeClient:
    last_error = None

    def __init__(self, snapshot):
        self._snapshot = snapshot

    def snapshot(self, *args, **kwargs):
        return self._snapshot

    def close(self):
        pass


def _settings(db):
    # Telegram unconfigured ⇒ send_message no-ops; no network.
    return Settings(
        watchlist=["EURUSD", "GBPUSD"],
        stance_db_path=db,
        heartbeat_seconds=300,
    )


def _snapshot():
    return {
        "equity": 10003.48,
        "balance": 10000.0,
        "margin": 5.0,
        "net_pnl": 3.48,
        "positions": [
            {"symbol": "EURUSD", "side": "BUY", "volume": 0.01,
             "entry_price": 1.1, "pnl": 3.5}
        ],
        "host": "demo",
    }


def test_tick_appends_audit_and_reads_stances(tmp_path):
    db = str(tmp_path / "bus.db")
    settings = _settings(db)
    stance_store.init_db(db)
    state.init_db(db)

    # Seed a fresh stance the heartbeat should pick up.
    stance_store.write_stance(
        db,
        Stance(
            instrument="EURUSD",
            direction="long",
            conviction=0.8,
            entry_zone=None,
            invalidation=1.09,
            target=1.13,
            rationale="bullish breakout",
            issued_at=datetime.now(timezone.utc),
            ttl_minutes=240,
        ),
    )

    client = FakeClient(_snapshot())
    heartbeat.tick(settings, client)

    # An audit row was appended and the chain verifies.
    last = state.get_last_decision(db)
    assert last is not None
    assert last["kind"] == "heartbeat"
    assert state.verify_chain(db)

    # The recorded stance directions reflect the live + stale instruments.
    import json

    payload = json.loads(last["payload"])
    assert payload["stances"]["EURUSD"] == "long"
    assert payload["stances"]["GBPUSD"] == "flat"  # no stance written
    assert payload["positions_count"] == 1


def test_tick_survives_snapshot_error(tmp_path):
    db = str(tmp_path / "bus.db")
    settings = _settings(db)
    client = FakeClient({"error": "cTrader not connected"})
    # Must not raise; should still append an audit row.
    heartbeat.tick(settings, client)
    assert state.get_last_decision(db) is not None
