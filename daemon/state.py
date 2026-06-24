"""Local audit + position state in SQLite.

The daemon appends a decision row every tick. Each row is hash-chained
(``sha256(prev_hash + canonical_payload)``) so the log is tamper-evident: any
edit to an old row breaks every hash after it. This fits the blueprint's audit
instinct (§4.1 step 5) without needing an external ledger.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone

GENESIS_HASH = "0" * 64


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS decisions (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        TEXT NOT NULL,
                kind      TEXT NOT NULL,
                payload   TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                hash      TEXT NOT NULL
            )
            """
        )


def _canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _row_hash(ts: str, kind: str, payload_json: str, prev_hash: str) -> str:
    digest = hashlib.sha256()
    digest.update(prev_hash.encode())
    digest.update(ts.encode())
    digest.update(kind.encode())
    digest.update(payload_json.encode())
    return digest.hexdigest()


def get_last_decision(db_path: str) -> sqlite3.Row | None:
    init_db(db_path)
    with _connect(db_path) as conn:
        return conn.execute(
            "SELECT * FROM decisions ORDER BY id DESC LIMIT 1"
        ).fetchone()


def append_decision(
    db_path: str, kind: str, payload: dict, ts: datetime | None = None
) -> str:
    """Append a hash-chained decision row. Returns the new row's hash."""
    init_db(db_path)
    ts_str = (ts or datetime.now(timezone.utc)).isoformat()
    payload_json = _canonical(payload)

    last = get_last_decision(db_path)
    prev_hash = last["hash"] if last else GENESIS_HASH
    row_hash = _row_hash(ts_str, kind, payload_json, prev_hash)

    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO decisions (ts, kind, payload, prev_hash, hash) "
            "VALUES (?, ?, ?, ?, ?)",
            (ts_str, kind, payload_json, prev_hash, row_hash),
        )
    return row_hash


def verify_chain(db_path: str) -> bool:
    """Recompute every row's hash and confirm the chain is intact."""
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM decisions ORDER BY id ASC").fetchall()
    prev_hash = GENESIS_HASH
    for row in rows:
        expected = _row_hash(row["ts"], row["kind"], row["payload"], prev_hash)
        if row["prev_hash"] != prev_hash or row["hash"] != expected:
            return False
        prev_hash = row["hash"]
    return True
