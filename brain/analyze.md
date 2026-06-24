# Analysis methodology (TradingAgents flow)

This is the reasoning the brain performs each run. The wired path executes it via
`TradingAgentsGraph.propagate()`; the optional Mode-A path has Claude perform it
directly as prompts. Either way the **output is a `Stance`, never a trade**.

## Inputs

- `instrument` (e.g. `EURUSD`) and `trade_date` (defaults to today, UTC).
- Market context: recent OHLCV + indicators, news/sentiment, macro. (Vendored
  TradingAgents data tools; equities-oriented — see the gap note below.)

## Flow (mirrors TradingAgents' graph)

1. **Analysts** — Market, Social/Sentiment, News, Fundamentals each produce a
   report from their data tools.
2. **Investment debate** — Bull vs Bear researchers argue; the **Research
   Manager** synthesizes an investment plan.
3. **Trader** — converts the plan into a concrete proposal: action (Buy/Hold/
   Sell), entry, **stop loss**, position sizing.
4. **Risk debate** — Aggressive / Conservative / Neutral analysts stress the
   proposal.
5. **Portfolio Manager** — issues the final 5-tier **rating** (Buy / Overweight
   / Hold / Underweight / Sell), an executive summary, and an optional **price
   target**.

## Output → Stance (see `write_stance.py`)

| Decision field | Stance field | Mapping |
|---|---|---|
| Rating Buy/Overweight | `direction=long` | conviction 0.8 / 0.6 |
| Rating Hold | `direction=flat` | conviction 0.0 |
| Rating Underweight/Sell | `direction=short` | conviction 0.6 / 0.8 |
| PM Price Target | `target` | parsed float |
| Trader Stop Loss | `invalidation` | parsed float (hard stop the daemon enforces) |
| Executive summary | `rationale` | short text for Telegram |
| — | `ttl_minutes` | from config (e.g. 240); stale ⇒ daemon flat |

## Gap to resolve before execution

TradingAgents reasons on tickers + **daily** news/fundamentals; cTrader is
intraday FX/CFD. Several data tools are equities-only. Define what "analyze
EURUSD" means (timeframe, which tools actually cover FX) before wiring Phase-3
execution to these stances.
