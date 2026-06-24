"""cTrader access-token auto-refresh.

cTrader Open API access tokens expire (~30 days); the bot otherwise dies silently
when the token lapses. This module refreshes the token via the OAuth endpoint and
persists the rotated credentials so unattended runs keep working — the key piece
that makes the no-Docker / Routine model viable long-term.

Endpoint (POST):
    https://openapi.ctrader.com/apps/token
      ?grant_type=refresh_token&refresh_token=...&client_id=...&client_secret=...
Response (JSON, camelCase): accessToken, refreshToken, expiresIn, tokenType,
errorCode, description.

NOTE: the refresh token ROTATES on every refresh — the response's refreshToken
replaces the old one. So we only refresh when near expiry (not every startup) and
always persist the new pair, or the next run's refresh token would be stale.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover - requests is a declared dependency
    requests = None

DEFAULT_TOKEN_URL = "https://openapi.ctrader.com/apps/token"


class TokenRefreshError(RuntimeError):
    pass


def refresh_token_pair(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    base_url: str | None = None,
    timeout: float = 15.0,
) -> dict:
    """Exchange a refresh token for a fresh access/refresh pair.

    Returns ``{access_token, refresh_token, expires_in, token_type}``.
    Raises TokenRefreshError on any failure.
    """
    if requests is None:
        raise TokenRefreshError("the 'requests' package is required for token refresh")
    if not all([client_id, client_secret, refresh_token]):
        raise TokenRefreshError("missing client_id / client_secret / refresh_token")

    url = base_url or os.getenv("TOKEN_REFRESH_URL", DEFAULT_TOKEN_URL)
    try:
        resp = requests.post(
            url,
            params={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Accept": "application/json"},
            timeout=timeout,
        )
    except Exception as exc:  # network failure
        raise TokenRefreshError(f"token refresh request failed: {exc}") from exc

    try:
        data = resp.json()
    except ValueError as exc:
        raise TokenRefreshError(f"token refresh returned non-JSON: {resp.text[:200]}") from exc

    if data.get("errorCode"):
        raise TokenRefreshError(
            f"token refresh rejected: {data.get('errorCode')} — {data.get('description')}"
        )

    access = data.get("accessToken")
    new_refresh = data.get("refreshToken")
    if not access or not new_refresh:
        raise TokenRefreshError(f"token refresh missing fields: {data}")

    return {
        "access_token": access,
        "refresh_token": new_refresh,
        "expires_in": int(data.get("expiresIn", 0) or 0),
        "token_type": data.get("tokenType", "bearer"),
    }


def update_env_file(env_path: str | Path, updates: dict[str, str]) -> None:
    """Idempotently set KEY=value lines in a .env file (create if missing)."""
    path = Path(env_path)
    lines = path.read_text().splitlines() if path.exists() else []
    remaining = dict(updates)

    out = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in remaining:
                out.append(f"{key}={remaining.pop(key)}")
                continue
        out.append(line)
    for key, value in remaining.items():
        out.append(f"{key}={value}")

    path.write_text("\n".join(out) + "\n")


def _expires_at(env: dict) -> datetime | None:
    raw = env.get("ACCESS_TOKEN_EXPIRES_AT")
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def ensure_fresh(
    env_path: str | Path | None = None,
    buffer_hours: float = 24.0,
    force: bool = False,
    now: datetime | None = None,
    env: dict | None = None,
) -> str | None:
    """Refresh the access token if it is near expiry; persist + update os.environ.

    Reads credentials from ``env`` (defaults to ``os.environ``). Only refreshes
    when ``force`` is set, or when ``ACCESS_TOKEN_EXPIRES_AT`` is known and within
    ``buffer_hours`` of now — this avoids rotating the refresh token needlessly on
    every startup. Never raises: on any problem it logs and returns the existing
    access token, so a refresh hiccup can't break startup.

    Returns the access token currently in effect (possibly unchanged).
    """
    env = env if env is not None else os.environ
    now = now or datetime.now(timezone.utc)
    current = env.get("ACCESS_TOKEN")

    if not force:
        expires_at = _expires_at(env)
        if expires_at is None:
            # Unknown expiry ⇒ don't auto-rotate; rely on the explicit CLI.
            return current
        if now + timedelta(hours=buffer_hours) < expires_at:
            return current  # still well within validity

    try:
        pair = refresh_token_pair(
            env.get("CLIENT_ID"),
            env.get("CLIENT_SECRET"),
            env.get("REFRESH_TOKEN"),
        )
    except TokenRefreshError as exc:
        print(f"[token_refresh] skipped: {exc}")
        return current

    expires_at_iso = (
        now + timedelta(seconds=pair["expires_in"])
    ).isoformat() if pair["expires_in"] else ""

    # Update the live process environment so the bot picks up the fresh token.
    os.environ["ACCESS_TOKEN"] = pair["access_token"]
    os.environ["REFRESH_TOKEN"] = pair["refresh_token"]
    if expires_at_iso:
        os.environ["ACCESS_TOKEN_EXPIRES_AT"] = expires_at_iso

    # Persist for the next run, if we have a writable env file.
    if env_path:
        try:
            update_env_file(
                env_path,
                {
                    "ACCESS_TOKEN": pair["access_token"],
                    "REFRESH_TOKEN": pair["refresh_token"],
                    **({"ACCESS_TOKEN_EXPIRES_AT": expires_at_iso} if expires_at_iso else {}),
                },
            )
        except Exception as exc:  # persistence is best-effort
            print(f"[token_refresh] refreshed but could not persist to {env_path}: {exc}")

    print("[token_refresh] access token refreshed.")
    return pair["access_token"]
