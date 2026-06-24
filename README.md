# algo-trader-bot

A Claude-driven trading assistant that fuses two upstream projects into one
decoupled system: a fast **daemon** that executes within risk rails and a slow
**brain** that reasons. See [`ALGO_TRADER_BOT_BLUEPRINT.md`](ALGO_TRADER_BOT_BLUEPRINT.md)
for the full design and locked decisions.

## Two ways to run

**A — Claude-direct, no Docker, no host (recommended).** Claude Code attaches the
cTrader MCP server and trades directly on a slow cadence (a scheduled Routine).
Nothing runs 24/7: the MCP is spawned per session, and broker-side SL/TP holds
your risk between runs. Safety is enforced in code by `mcp/ctrader/risk_gate.py`.

**B — 24/7 daemon (optional, needs an always-on host).** A plain-Python loop
(`daemon/`) reads a `Stance` from the bus and executes within `daemon/risk.py`
rails; the `brain/` writes stances on a slow cadence. Containerized in `deploy/`.

## Layout

```
mcp/ctrader/          # vendored fork of ctrader-mcp-server (MIT) — the cTrader core + MCP
  ├─ server.py        #   MCP tools (read + trade), hardened with a risk gate
  ├─ risk_gate.py     #   demo gate, mandatory SL, caps, kill switch (path A)
  ├─ indicators.py    #   pandas/numpy technical indicators
  └─ token_refresh.py #   auto-refresh the cTrader access token near expiry
agents/tradingagents/ # vendored fork of TradingAgents (Apache-2.0) — reasoning graph
routine/CLAUDE.md     # standing instructions for the Claude-direct trading Routine (path A)
daemon/               # optional 24/7 muscle (path B): heartbeat, stance bus, risk
brain/                # optional slow-cadence reasoning that emits a Stance (path B)
deploy/               # Dockerfile, docker-compose, .env.example (path B)
scripts/              # setup.sh, refresh_token.py
tests/                # unit tests (no credentials needed)
```

## Quick start — no Docker (path A)

```bash
bash scripts/setup.sh                 # venv + deps + .env from template
#   Windows: python -m venv .venv; .venv\Scripts\activate; pip install -r requirements.txt

# 1) Fill in .env: CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, REFRESH_TOKEN,
#    ACCOUNT_ID (ctidTraderAccountId), HOST=demo
# 2) (optional) mint a fresh token now and save it back to .env:
python scripts/refresh_token.py

# 3) Trade via Claude Code: the repo-root .mcp.json auto-attaches the cTrader MCP.
#    Export the cTrader creds in your shell first (or set them in your Claude Code
#    cloud environment), then run a session/Routine driven by routine/CLAUDE.md.
```

Claude then calls the MCP tools (`get_account_status`, `get_historical_data`,
`get_indicator`, `create_market_order` with a mandatory `stop_loss`, …). The
risk gate rejects unsafe orders before they reach the broker.

### Token refresh

cTrader access tokens expire (~30 days). `mcp/ctrader/token_refresh.py` refreshes
automatically at startup when the token is near expiry (it needs `REFRESH_TOKEN`),
persisting the rotated pair back to `.env`. Force a refresh anytime with
`python scripts/refresh_token.py` — handy as a monthly cron / scheduled Routine.

## Optional — 24/7 daemon (path B)

```bash
python -m daemon.heartbeat           # 5-min snapshot heartbeat to Telegram (no trading)
python -m brain.run_analysis EURUSD  # slow-cadence reasoning → Stance (needs API key)
```

## Tests

```bash
python -m pytest tests/ -q           # no credentials required
```

## Safety

`HOST=demo` is the default; live requires `LIVE_CONFIRMED=1`. Every entry order
must carry a `stop_loss` (`REQUIRE_STOP_LOSS`), and per-order/position caps apply
(`MAX_ORDER_LOTS`, `MAX_POSITIONS`). The kill switch is the sentinel file `./HALT`
(`touch HALT` to stop new orders). Live trading is a separate, gated milestone
after a long demo soak.
