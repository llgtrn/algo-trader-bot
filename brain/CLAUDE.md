# Brain — standing instructions

This directory is the **brain**: the slow-cadence reasoning half of
algo-trader-bot. It runs the TradingAgents multi-agent analysis and emits a
`Stance` per instrument onto the shared bus. The **daemon** (see `../daemon/`)
is the only component that ever places an order; the brain never executes.

## What a brain run does

1. Pick the instrument(s) from the watchlist.
2. Run the reasoning flow (see `analyze.md`) — either:
   - **Wired path (current):** `python -m brain.run_analysis <INSTRUMENT>` calls
     `TradingAgentsGraph.propagate()` and maps the result to a `Stance`.
   - **Mode-A path (future option):** a Claude Code scheduled task executes the
     `analyze.md` methodology itself (no API key) and calls
     `brain.write_stance.emit_stance(...)`.
3. The mapping (rating → direction/conviction, price target, stop) lives in
   `write_stance.py` — the single source of truth. Do not duplicate it.

## Cadence (non-negotiable)

- Run **1–24 times per day**, never on the 5-minute tick.
- Each run is a full reasoning pass; the daemon already handles the fast loop.
- If runs stop (usage limits, errors), the daemon sees **stale stances → flat**
  and keeps reporting. Watch for a stale-stance alert.

## Requirements for the wired path

```
TRADINGAGENTS_LLM_PROVIDER=anthropic
TRADINGAGENTS_DEEP_THINK_LLM=<deep model>
TRADINGAGENTS_QUICK_THINK_LLM=<quick model>
ANTHROPIC_API_KEY=...
STANCE_DB_PATH=./algo-trader-bot.db   # must match the daemon's bus
```

## Known gaps (carried from the blueprint)

- **Asset semantics:** TradingAgents is equities/daily-oriented. FX/CFD intraday
  data is not covered; the brain currently reasons on daily context. Defining
  what "analyze EURUSD" means is the biggest open design question.
- **Stop derivation:** if the Trader omits a stop, `invalidation` is `None` and
  the daemon will not auto-stop. Tighten this before enabling execution.
