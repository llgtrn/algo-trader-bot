import sqlite3

from daemon.state import append_decision, get_last_decision, verify_chain


def test_chain_links_rows(tmp_path):
    db = str(tmp_path / "audit.db")
    h1 = append_decision(db, "heartbeat", {"n": 1})
    h2 = append_decision(db, "heartbeat", {"n": 2})
    assert h1 != h2

    last = get_last_decision(db)
    assert last["hash"] == h2
    assert last["prev_hash"] == h1
    assert verify_chain(db)


def test_tamper_breaks_chain(tmp_path):
    db = str(tmp_path / "audit.db")
    append_decision(db, "heartbeat", {"n": 1})
    append_decision(db, "heartbeat", {"n": 2})
    assert verify_chain(db)

    # Mutate an old payload directly — the chain must no longer verify.
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE decisions SET payload = ? WHERE id = 1", ('{"n":99}',))
    assert not verify_chain(db)


def test_empty_chain_verifies(tmp_path):
    db = str(tmp_path / "audit.db")
    assert verify_chain(db)
    assert get_last_decision(db) is None
