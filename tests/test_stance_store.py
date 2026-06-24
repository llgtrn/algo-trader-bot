from datetime import datetime, timedelta, timezone

from daemon.stance_store import Stance, read_latest, write_stance


def _stance(instrument="EURUSD", issued_at=None, ttl=240, direction="long"):
    return Stance(
        instrument=instrument,
        direction=direction,
        conviction=0.8,
        entry_zone=(1.10, 1.11),
        invalidation=1.09,
        target=1.13,
        rationale="test",
        issued_at=issued_at or datetime.now(timezone.utc),
        ttl_minutes=ttl,
    )


def test_round_trip(tmp_path):
    db = str(tmp_path / "bus.db")
    write_stance(db, _stance())
    got = read_latest(db, "EURUSD")
    assert got is not None
    assert got.direction == "long"
    assert got.entry_zone == (1.10, 1.11)
    assert got.target == 1.13


def test_missing_returns_none(tmp_path):
    db = str(tmp_path / "bus.db")
    assert read_latest(db, "GBPUSD") is None


def test_stale_returns_none(tmp_path):
    db = str(tmp_path / "bus.db")
    old = datetime.now(timezone.utc) - timedelta(minutes=300)
    write_stance(db, _stance(issued_at=old, ttl=240))
    # 300 min old with a 240 min TTL ⇒ stale ⇒ flat/None.
    assert read_latest(db, "EURUSD") is None


def test_latest_wins(tmp_path):
    db = str(tmp_path / "bus.db")
    write_stance(db, _stance(direction="long"))
    write_stance(db, _stance(direction="short"))
    got = read_latest(db, "EURUSD")
    assert got is not None and got.direction == "short"


def test_is_stale_naive_datetime():
    old = datetime.utcnow() - timedelta(minutes=10)  # naive
    assert _stance(issued_at=old, ttl=5).is_stale()
    assert not _stance(issued_at=old, ttl=60).is_stale()
