"""Direct cTrader access for the daemon (blueprint "Option 1").

Imports ``SimpleCTraderBot`` from the vendored cTrader core and drives it from a
background Twisted reactor thread — the pattern proven in
``mcp/ctrader/server.py`` (initialize_bot). The daemon talks to ONE persistent
socket; no MCP transport in the hot path.

Phase 1 exposes a single read method, ``snapshot()``. Order methods are NOT
wired here — execution arrives in Phase 3 under risk.py rails.

NOTE(token-refresh): cTrader access tokens expire and SimpleCTraderBot has no
refresh logic. Deferred to a later phase; for now a token expiry surfaces as an
auth failure / stale snapshot, which the heartbeat reports.
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

# Make the vendored cTrader core importable: mcp/ctrader holds ctrader_bot.py
# and uses package-root-relative imports (``from ctrader_bot import ...``).
_CTRADER_ROOT = Path(__file__).resolve().parent.parent / "mcp" / "ctrader"
if str(_CTRADER_ROOT) not in sys.path:
    sys.path.insert(0, str(_CTRADER_ROOT))


class CTraderClient:
    """Thin, daemon-friendly wrapper over SimpleCTraderBot."""

    def __init__(self, connect_timeout: float = 30.0):
        self.connect_timeout = connect_timeout
        self._bot = None
        self._reactor = None
        self._thread: threading.Thread | None = None
        self.last_error: str | None = None

    # ------------------------------------------------------------------ connect
    def connect(self) -> bool:
        """Start the bot + reactor thread and wait for full authentication.

        Returns True once connected, app-authed, account-authed and symbols are
        loaded; False on timeout, missing dependency, or missing credentials.
        Never raises — the daemon must keep running and report the failure.
        """
        try:
            from twisted.internet import reactor  # default reactor; no asyncio

            from ctrader_bot import SimpleCTraderBot

            self._reactor = reactor
            self._bot = SimpleCTraderBot()  # validates credentials in __init__
        except ImportError as exc:
            self.last_error = f"missing dependency: {exc}"
            return False
        except ValueError as exc:
            self.last_error = f"bad/missing credentials: {exc}"
            return False

        def _run():
            self._bot.start()
            if not reactor.running:
                reactor.run(installSignalHandlers=False)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

        deadline = time.time() + self.connect_timeout
        while time.time() < deadline:
            if self._is_ready():
                self.last_error = None
                return True
            time.sleep(1)
        self.last_error = "auth timeout (not connected/authenticated in time)"
        return False

    def _is_ready(self) -> bool:
        bot = self._bot
        return bool(
            bot
            and bot.is_connected
            and bot.is_app_authenticated
            and bot.is_account_authenticated
            and len(bot.symbols) > 0
        )

    # ----------------------------------------------------------------- snapshot
    def snapshot(self, reconcile_wait: float = 2.0) -> dict:
        """Return a live account snapshot.

        Triggers a server-side reconcile (positions/orders/account) on the
        reactor thread, waits briefly for the async response, then assembles a
        plain dict. On any failure returns ``{"error": "..."}`` so the heartbeat
        degrades gracefully instead of crashing.
        """
        if not self._is_ready():
            return {"error": "cTrader not connected/authenticated"}

        try:
            # Cross-thread: schedule the reconcile send on the reactor thread.
            self._reactor.callFromThread(self._bot.refresh_positions)
            time.sleep(reconcile_wait)  # let the async reconcile response land

            status = self._bot.get_account_status() or {}
            positions = [self._enrich_position(p) for p in self._bot.positions]

            snap = dict(status)
            snap["positions"] = positions
            snap["host"] = self._bot.host_type
            return snap
        except Exception as exc:  # noqa: BLE001 - degrade, never crash the loop
            return {"error": f"snapshot failed: {exc}"}

    def _enrich_position(self, pos: dict) -> dict:
        """Attach the human symbol name to a raw position dict."""
        symbol_name = next(
            (
                s["name"]
                for s in self._bot.symbols.values()
                if s["id"] == pos.get("symbol_id")
            ),
            None,
        )
        enriched = dict(pos)
        enriched["symbol"] = symbol_name or pos.get("symbol_id")
        return enriched

    # ------------------------------------------------------------------ shutdown
    def close(self) -> None:
        if self._reactor is not None and self._reactor.running:
            self._reactor.callFromThread(self._reactor.stop)
