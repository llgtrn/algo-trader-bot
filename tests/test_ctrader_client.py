"""Integration test for CTraderClient.snapshot() using injected fakes.

No twisted / ctrader-open-api / credentials needed: we set the private
``_bot`` and ``_reactor`` attributes directly and exercise the read path.
"""

from daemon.ctrader_client import CTraderClient


class FakeReactor:
    running = True

    def callFromThread(self, fn, *args, **kwargs):
        # Run inline so the test is deterministic (no real reactor thread).
        fn(*args, **kwargs)


class FakeBot:
    def __init__(self):
        self.is_connected = True
        self.is_app_authenticated = True
        self.is_account_authenticated = True
        self.host_type = "demo"
        self.symbols = {
            "EURUSD": {"id": 1, "name": "EURUSD", "digits": 5},
            "GBPUSD": {"id": 2, "name": "GBPUSD", "digits": 5},
        }
        self.positions = [
            {
                "id": 111,
                "symbol_id": 1,
                "volume": 0.01,
                "side": "BUY",
                "entry_price": 1.1000,
                "swap": 0.0,
                "commission": -0.02,
                "pnl": 3.50,
            }
        ]
        self.refreshed = False

    def refresh_positions(self):
        self.refreshed = True

    def get_account_status(self):
        return {
            "account_id": 42,
            "positions_count": len(self.positions),
            "orders_count": 0,
            "net_pnl": 3.48,
            "balance": 10000.0,
            "equity": 10003.48,
            "margin": 5.0,
        }


def _client_with_fakes():
    client = CTraderClient()
    client._bot = FakeBot()
    client._reactor = FakeReactor()
    return client


def test_snapshot_assembles_account_and_positions():
    client = _client_with_fakes()
    snap = client.snapshot(reconcile_wait=0)

    assert "error" not in snap
    assert snap["equity"] == 10003.48
    assert snap["net_pnl"] == 3.48
    assert snap["host"] == "demo"
    assert client._bot.refreshed is True  # reconcile was triggered

    assert len(snap["positions"]) == 1
    pos = snap["positions"][0]
    assert pos["symbol"] == "EURUSD"  # symbol_id → human name enrichment
    assert pos["side"] == "BUY"
    assert pos["pnl"] == 3.50


def test_snapshot_unready_returns_error():
    client = CTraderClient()  # no bot injected → not ready
    snap = client.snapshot(reconcile_wait=0)
    assert "error" in snap


def test_snapshot_handles_missing_account_info():
    client = _client_with_fakes()
    client._bot.get_account_status = lambda: None  # cTrader not yet reconciled
    snap = client.snapshot(reconcile_wait=0)
    assert "error" not in snap
    assert snap["positions"]  # positions still surface
