import sys
from pathlib import Path

import pytest

# risk_gate lives in mcp/ctrader (package-root style import).
_GATE_ROOT = Path(__file__).resolve().parent.parent / "mcp" / "ctrader"
if str(_GATE_ROOT) not in sys.path:
    sys.path.insert(0, str(_GATE_ROOT))

import risk_gate  # noqa: E402


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    """Deterministic defaults: demo host, kill switch absent, caps unset."""
    for var in ["HOST", "LIVE_CONFIRMED", "MAX_ORDER_LOTS", "MAX_POSITIONS",
                "REQUIRE_STOP_LOSS"]:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("KILL_SWITCH_FILE", str(tmp_path / "HALT"))
    monkeypatch.setenv("HOST", "demo")
    return monkeypatch


def test_entry_allowed_with_stop():
    r = risk_gate.check_order(is_entry=True, volume=0.01, stop_loss=1.09)
    assert r.allowed


def test_entry_rejected_without_stop():
    r = risk_gate.check_order(is_entry=True, volume=0.01, stop_loss=None)
    assert not r.allowed and "stop_loss" in r.reason


def test_require_stop_loss_can_be_disabled(clean_env):
    clean_env.setenv("REQUIRE_STOP_LOSS", "0")
    r = risk_gate.check_order(is_entry=True, volume=0.01, stop_loss=None)
    assert r.allowed


def test_live_gate_blocks_unconfirmed(clean_env):
    clean_env.setenv("HOST", "live")
    r = risk_gate.check_order(is_entry=True, volume=0.01, stop_loss=1.09)
    assert not r.allowed and "LIVE_CONFIRMED" in r.reason


def test_live_gate_allows_confirmed(clean_env):
    clean_env.setenv("HOST", "live")
    clean_env.setenv("LIVE_CONFIRMED", "1")
    r = risk_gate.check_order(is_entry=True, volume=0.01, stop_loss=1.09)
    assert r.allowed


def test_kill_switch_blocks_entry(clean_env, tmp_path):
    sentinel = tmp_path / "HALT"
    sentinel.write_text("")
    r = risk_gate.check_order(is_entry=True, volume=0.01, stop_loss=1.09)
    assert not r.allowed and "kill switch" in r.reason


def test_kill_switch_does_not_block_close(clean_env, tmp_path):
    (tmp_path / "HALT").write_text("")
    # Risk-reducing (close/cancel) always allowed, even with kill switch on.
    r = risk_gate.check_order(is_entry=False)
    assert r.allowed


def test_max_order_lots(clean_env):
    clean_env.setenv("MAX_ORDER_LOTS", "0.10")
    assert not risk_gate.check_order(is_entry=True, volume=0.5, stop_loss=1.0).allowed
    assert risk_gate.check_order(is_entry=True, volume=0.05, stop_loss=1.0).allowed


def test_max_positions(clean_env):
    clean_env.setenv("MAX_POSITIONS", "3")
    r = risk_gate.check_order(is_entry=True, volume=0.01, stop_loss=1.0, open_positions=3)
    assert not r.allowed and "MAX_POSITIONS" in r.reason
    ok = risk_gate.check_order(is_entry=True, volume=0.01, stop_loss=1.0, open_positions=2)
    assert ok.allowed
