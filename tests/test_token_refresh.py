import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent / "mcp" / "ctrader"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import token_refresh as tr  # noqa: E402


# ----------------------------------------------------------------- env file I/O
def test_update_env_file_creates_and_updates(tmp_path):
    env = tmp_path / ".env"
    env.write_text("CLIENT_ID=abc\nACCESS_TOKEN=old\n# comment\n")
    tr.update_env_file(env, {"ACCESS_TOKEN": "new", "REFRESH_TOKEN": "r2"})
    text = env.read_text()
    assert "ACCESS_TOKEN=new" in text
    assert "REFRESH_TOKEN=r2" in text  # appended
    assert "CLIENT_ID=abc" in text  # untouched
    assert "# comment" in text  # comments preserved


def test_update_env_file_when_missing(tmp_path):
    env = tmp_path / ".env"
    tr.update_env_file(env, {"ACCESS_TOKEN": "x"})
    assert env.read_text().strip() == "ACCESS_TOKEN=x"


# --------------------------------------------------------------- refresh parsing
class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_refresh_token_pair_success(monkeypatch):
    captured = {}

    def fake_post(url, params=None, headers=None, timeout=None):
        captured["url"] = url
        captured["params"] = params
        return _Resp({
            "accessToken": "AT2", "refreshToken": "RT2",
            "expiresIn": 2628000, "tokenType": "bearer", "errorCode": None,
        })

    monkeypatch.setattr(tr.requests, "post", fake_post)
    out = tr.refresh_token_pair("cid", "secret", "RT1")
    assert out["access_token"] == "AT2"
    assert out["refresh_token"] == "RT2"
    assert out["expires_in"] == 2628000
    assert captured["params"]["grant_type"] == "refresh_token"
    assert captured["url"] == tr.DEFAULT_TOKEN_URL


def test_refresh_token_pair_error_code(monkeypatch):
    monkeypatch.setattr(
        tr.requests, "post",
        lambda *a, **k: _Resp({"errorCode": "INVALID_GRANT", "description": "bad"}),
    )
    with pytest.raises(tr.TokenRefreshError):
        tr.refresh_token_pair("cid", "secret", "RT1")


def test_refresh_missing_inputs():
    with pytest.raises(tr.TokenRefreshError):
        tr.refresh_token_pair("", "", "")


# --------------------------------------------------------------------- ensure_fresh
def _env(**overrides):
    base = {
        "CLIENT_ID": "cid", "CLIENT_SECRET": "secret", "REFRESH_TOKEN": "RT1",
        "ACCESS_TOKEN": "AT1",
    }
    base.update(overrides)
    return base


def test_ensure_fresh_skips_when_expiry_unknown(monkeypatch):
    called = {"n": 0}
    monkeypatch.setattr(tr, "refresh_token_pair", lambda *a, **k: called.__setitem__("n", 1))
    token = tr.ensure_fresh(env=_env())  # no ACCESS_TOKEN_EXPIRES_AT
    assert token == "AT1"
    assert called["n"] == 0  # never refreshed — avoids needless rotation


def test_ensure_fresh_skips_when_far_from_expiry(monkeypatch):
    called = {"n": 0}
    monkeypatch.setattr(tr, "refresh_token_pair", lambda *a, **k: called.__setitem__("n", 1))
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    far = (now + timedelta(days=10)).isoformat()
    token = tr.ensure_fresh(env=_env(ACCESS_TOKEN_EXPIRES_AT=far), now=now)
    assert token == "AT1" and called["n"] == 0


def test_ensure_fresh_refreshes_near_expiry(monkeypatch, tmp_path):
    monkeypatch.setattr(
        tr, "refresh_token_pair",
        lambda *a, **k: {"access_token": "AT2", "refresh_token": "RT2",
                         "expires_in": 2628000, "token_type": "bearer"},
    )
    # Use a real os.environ-like dict and a temp env file for persistence.
    env = _env(ACCESS_TOKEN_EXPIRES_AT=datetime.now(timezone.utc).isoformat())
    monkeypatch.setattr("os.environ", dict(env), raising=False)
    env_file = tmp_path / ".env"
    token = tr.ensure_fresh(env_path=env_file, env=env, force=False)
    assert token == "AT2"
    assert "ACCESS_TOKEN=AT2" in env_file.read_text()
    assert "REFRESH_TOKEN=RT2" in env_file.read_text()


def test_ensure_fresh_force(monkeypatch):
    monkeypatch.setattr(
        tr, "refresh_token_pair",
        lambda *a, **k: {"access_token": "AT9", "refresh_token": "RT9",
                         "expires_in": 0, "token_type": "bearer"},
    )
    monkeypatch.setattr("os.environ", {}, raising=False)
    token = tr.ensure_fresh(env=_env(), force=True)
    assert token == "AT9"


def test_ensure_fresh_survives_refresh_failure(monkeypatch):
    def boom(*a, **k):
        raise tr.TokenRefreshError("network down")
    monkeypatch.setattr(tr, "refresh_token_pair", boom)
    token = tr.ensure_fresh(env=_env(), force=True)
    assert token == "AT1"  # falls back to existing token, no raise
