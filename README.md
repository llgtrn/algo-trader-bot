# algo-trader-bot

A Claude-driven trading assistant that fuses two upstream projects into one
decoupled system: a fast **daemon** that executes within risk rails and a slow
**brain** that reasons. See [`ALGO_TRADER_BOT_BLUEPRINT.md`](ALGO_TRADER_BOT_BLUEPRINT.md)
for the full design and locked decisions.

## Layout

```
mcp/ctrader/          # vendored fork of ctrader-mcp-server (MIT) — the cTrader core
agents/tradingagents/ # vendored fork of TradingAgents (Apache-2.0) — the reasoning graph
daemon/               # NEW: 24/7 muscle (plain Python, no LLM)
brain/                # NEW: slow-cadence reasoning; runs TradingAgents, emits a Stance
deploy/               # Dockerfile, docker-compose, .env.example
tests/                # pure-Python unit tests (no credentials needed)
```

**Core principle:** loop and brain are decoupled by a `Stance` bus (SQLite). The
brain writes a stance; the daemon reads it and is the **only** thing that places
orders, always within `daemon/risk.py` rails. A stale or missing stance ⇒ flat.

## Status — Phase 0–1 (foundation, snapshot-only)

- ✅ Monorepo restructured to the blueprint layout.
- ✅ Daemon: 5-min heartbeat posts a real demo-account snapshot to Telegram.
  **No order placement yet** (execution is Phase 3).
- ✅ Stance bus (`daemon/stance_store.py`) + hash-chained audit
  (`daemon/state.py`).
- ✅ Risk gates (kill switch + demo/live gate) in place before any order code.
- ✅ Brain wired to `TradingAgentsGraph.propagate()` → `Stance`.

## Quick start

```bash
pip install -r requirements.txt
cp deploy/.env.example .env          # fill in cTrader + Telegram creds (HOST=demo)
python -m daemon.heartbeat           # 5-min heartbeat to Telegram (no trading)

# Brain (needs an API key, slow cadence only):
python -m brain.run_analysis EURUSD
```

Run the tests (no credentials required):

```bash
python -m pytest tests/ -q
```

## Safety

`HOST=demo` is the default; live requires `LIVE_CONFIRMED=1`. The kill switch is
the sentinel file `./HALT` (`touch HALT` to stop new orders). Live trading is a
separate, gated milestone after a long demo soak.
