"""The Stance contract and its SQLite-backed bus.

The brain (slow cadence, Claude) writes a ``Stance`` per instrument; the daemon
(5-min tick) reads the latest one. A co-located host means the simplest possible
bus: a shared local SQLite file.

Core rule (blueprint §3): a stale or missing stance is treated as FLAT — the
daemon takes no action on it. ``read_latest`` enforces this by returning ``None``
when the most recent stance has aged past its TTL.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class Stance:
    """A trading stance: the only thing the brain hands to the daemon."""

    instrument: str  # "EURUSD"
    direction: str  # "long" | "short" | "flat"
    conviction: float  # 0.0–1.0
    entry_zone: tuple | None  # (lo, hi) or None for market
    invalidation: float | None  # hard stop level → daemon enforces (Phase 3)
    target: float | None
    rationale: str  # short, for Telegram
    issued_at: datetime
    ttl_minutes: int  # e.g. 240; stale stance ⇒ daemon treats as "flat"

    def is_stale(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        issued = self.issued_at
        if issued.tzinfo is None:
            issued = issued.replace(tzinfo=timezone.utc)
        return now > issued + timedelta(minutes=self.ttl_minutes)


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    """Create the stances table if it does not exist."""
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stances (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument   TEXT NOT NULL,
                direction    TEXT NOT NULL,
                conviction   REAL NOT NULL,
                entry_zone   TEXT,
                invalidation REAL,
                target       REAL,
                rationale    TEXT,
                issued_at    TEXT NOT NULL,
                ttl_minutes  INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_stances_instrument "
            "ON stances(instrument, id DESC)"
        )


def write_stance(db_path: str, stance: Stance) -> None:
    """Persist a stance to the bus. The brain calls this (via brain.write_stance)."""
    init_db(db_path)
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO stances
                (instrument, direction, conviction, entry_zone, invalidation,
                 target, rationale, issued_at, ttl_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stance.instrument,
                stance.direction,
                stance.conviction,
                json.dumps(stance.entry_zone) if stance.entry_zone is not None else None,
                stance.invalidation,
                stance.target,
                stance.rationale,
                stance.issued_at.isoformat(),
                stance.ttl_minutes,
            ),
        )


def _row_to_stance(row: sqlite3.Row) -> Stance:
    entry_zone = json.loads(row["entry_zone"]) if row["entry_zone"] else None
    if entry_zone is not None:
        entry_zone = tuple(entry_zone)
    return Stance(
        instrument=row["instrument"],
        direction=row["direction"],
        conviction=row["conviction"],
        entry_zone=entry_zone,
        invalidation=row["invalidation"],
        target=row["target"],
        rationale=row["rationale"],
        issued_at=datetime.fromisoformat(row["issued_at"]),
        ttl_minutes=row["ttl_minutes"],
    )


def read_latest(
    db_path: str, instrument: str, now: datetime | None = None
) -> Stance | None:
    """Return the newest non-stale stance for ``instrument``, else ``None``.

    A missing row OR a stance past its TTL both yield ``None`` — the daemon
    interprets that as FLAT (no action).
    """
    init_db(db_path)
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM stances WHERE instrument = ? ORDER BY id DESC LIMIT 1",
            (instrument.upper(),),
        ).fetchone()
    if row is None:
        return None
    stance = _row_to_stance(row)
    if stance.is_stale(now):
        return None
    return stance


def to_dict(stance: Stance) -> dict:
    """JSON-friendly view (issued_at as ISO string)."""
    data = asdict(stance)
    data["issued_at"] = stance.issued_at.isoformat()
    return data
