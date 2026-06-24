import pytest

from daemon.config import Settings
from daemon.risk import demo_gate, is_halted, within_caps


def test_kill_switch_sentinel(tmp_path):
    sentinel = tmp_path / "HALT"
    settings = Settings(kill_switch_file=str(sentinel))
    assert not is_halted(settings)
    sentinel.write_text("")
    assert is_halted(settings)


def test_demo_gate_allows_demo():
    demo_gate(Settings(host="demo"))  # no raise


def test_demo_gate_blocks_unconfirmed_live():
    with pytest.raises(RuntimeError):
        demo_gate(Settings(host="live", live_confirmed=False))


def test_demo_gate_allows_confirmed_live():
    demo_gate(Settings(host="live", live_confirmed=True))  # no raise


def test_within_caps_unset_is_ok():
    # All caps 0/unset ⇒ nothing enforced.
    snap = {"positions": [{"volume": 5.0}], "net_pnl": -1000}
    ok, _ = within_caps(Settings(), snap)
    assert ok


def test_within_caps_max_positions():
    settings = Settings(max_positions=1)
    snap = {"positions": [{"volume": 1.0}, {"volume": 1.0}]}
    ok, reason = within_caps(settings, snap)
    assert not ok and "max_positions" in reason


def test_within_caps_max_lots():
    settings = Settings(max_lots=1.0)
    snap = {"positions": [{"volume": 0.6}, {"volume": 0.6}]}
    ok, reason = within_caps(settings, snap)
    assert not ok and "max_lots" in reason


def test_within_caps_daily_loss():
    settings = Settings(max_daily_loss=500)
    snap = {"positions": [], "net_pnl": -600}
    ok, reason = within_caps(settings, snap)
    assert not ok and "max_daily_loss" in reason
