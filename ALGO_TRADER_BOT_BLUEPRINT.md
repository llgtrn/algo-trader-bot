# algo-trader-bot — Fork & Integration Blueprint (v2, decisions locked)

**Goal:** Fork `akinabudu/ctrader-mcp-server` (MIT) + `TauricResearch/TradingAgents` (Apache-2.0) into one Claude-driven trading assistant that gets real-time data and executes via cTrader, reasons with TradingAgents-style multi-agent analysis, runs autonomously on cloud, reports to Telegram with a 5-minute heartbeat, and uses **Claude as the LLM with no API key**.

---

## 0. Locked decisions

| Decision | Choice | Consequence |
|---|---|---|
| **Brain mode** | **Mode A** — Claude via subscription / Claude Code Routine | No API key. Claude is the LLM. Bounded by plan usage limits, so brain runs on a **slow cadence only**. |
| **cTrader access (loop)** | **Option 1** — `import ctrader_bot` directly in `ctrader_client.py`, no MCP transport | Fast, persistent socket. Implies the heartbeat is a **long-lived Python daemon**, not a Routine. |
| **Heartbeat** | **Plain Python daemon** on an always-on host | Runs the 5-min tick 24/7, no LLM. |
| **Brain trigger** | **Claude Code scheduled task / Routine** | Runs TradingAgents reasoning on slow cadence, writes a `Stance`. |

### Why the heartbeat is NOT a Claude Code Routine
Routines are real and fit Mode A (Claude as LLM, no key, runs even with laptop off). But **each scheduled run starts a full Claude Code session and counts against plan usage limits.** A 5-min heartbeat = 288 sessions/day → blows through Pro, strains Max, and is wasteful (spinning up a reasoning agent to print P&L and check a stop). Cloud runs are also cold-clone + carry timing jitter — wrong for a reactive tick. So: **daemon = muscle (5 min, no LLM); Routine = brain (hourly/on-signal, Claude).**

---

## 1. Architecture

```
                         ┌──────────────────────────────────────────┐
                         │     ALWAYS-ON HOST (VPS or your machine)   │
   cTrader ◀──Open API───┤                                            │
   (TCP 5035 demo /      │  heartbeat daemon (plain Python, 24/7)     │
    5034 live)           │   ├─ ctrader_client.py  (imports          │
                         │   │     ctrader_bot directly — Option 1)   │
                         │   ├─ risk.py   (caps, kill switch, gate)   │
                         │   ├─ state.py  (SQLite: pos/decisions)     │
   Telegram ◀────────────┤   └─ telegram.py (heartbeat, alerts, cmds) │
                         │            ▲ reads latest Stance           │
                         │   ┌────────┴───────────┐                   │
                         │   │   STANCE BUS        │  (SQLite file /   │
                         │   │  (shared store)     │   Drive / git)    │
                         │   └────────▲───────────┘                   │
                         │            │ writes Stance                 │
                         └────────────┼──────────────────────────────┘
                                      │  slow cadence (hourly/on-signal)
                        ┌─────────────┴───────────────────────────────┐
                        │  BRAIN = Claude Code scheduled task / Routine │
                        │   • cTrader MCP + data MCP attached           │
                        │   • runs TradingAgents reasoning as prompts   │
                        │   • Claude = LLM (subscription, NO API key)   │
                        │   • output: Stance JSON → Stance bus          │
                        └───────────────────────────────────────────────┘
```

**Core principle:** loop and brain are decoupled. The daemon runs forever and is boring. The brain is expensive, runs rarely, and only emits a `Stance`. The daemon is the **only** thing that places orders, and only within `risk.py` rails.

---

## 2. Monorepo layout

```
algo-trader-bot/
├── mcp/ctrader/              # fork of akinabudu/ctrader-mcp-server
│   ├── server.py             #   MCP tool surface — used by the BRAIN Routine
│   ├── ctrader_bot.py        #   Open API wrapper (Spotware OpenApiPy) — SHARED CORE
│   └── ...
├── agents/tradingagents/     # fork of TauricResearch/TradingAgents
│   ├── tradingagents/        #   graph/, agents/, data tools — reasoning logic
│   └── ...
├── daemon/                   # NEW — the 24/7 muscle (plain Python)
│   ├── heartbeat.py          #   5-min loop
│   ├── ctrader_client.py     #   imports agents'... ctrader_bot directly (Option 1)
│   ├── risk.py               #   caps, kill switch, demo/live gate
│   ├── telegram.py           #   bot: heartbeat, alerts, inbound commands
│   ├── state.py              #   SQLite: positions, decisions (audit rows, hashed)
│   ├── stance_store.py       #   read/write the Stance bus
│   └── config.py             #   watchlist, cadences, limits
├── brain/                    # NEW — the slow-cadence reasoning, run by Claude Code
│   ├── CLAUDE.md             #   standing instructions for the Routine
│   ├── analyze.md            #   the deep-analysis prompt body (TradingAgents flow)
│   └── write_stance.py       #   helper the Routine calls to emit Stance JSON
└── deploy/
    ├── Dockerfile            #   daemon container
    ├── docker-compose.yml
    └── .env.example
```

`ctrader_bot.py` is the shared core: the daemon imports it directly (Option 1); the MCP server wraps it for the brain. Both reuse one cTrader integration.

---

## 3. The Stance contract (bus between brain and daemon)

```python
@dataclass
class Stance:
    instrument: str          # "EURUSD"
    direction: str           # "long" | "short" | "flat"
    conviction: float        # 0.0–1.0
    entry_zone: tuple | None # (lo, hi) or None for market
    invalidation: float      # hard stop level → daemon enforces
    target: float | None
    rationale: str           # short, for Telegram
    issued_at: datetime
    ttl_minutes: int         # e.g. 240; stale stance ⇒ daemon treats as "flat"
```

The brain Routine produces these; the daemon consumes them. **Stale or missing stance ⇒ flat (no action).**

---

## 4. The two processes

### 4.1 Heartbeat daemon (`daemon/`, plain Python, 24/7)
Per 5-min tick:
1. Live snapshot from cTrader via `ctrader_client` (direct `ctrader_bot` import): prices, open positions, equity, margin, P&L.
2. Load latest `Stance` per instrument from `stance_store` (stale/missing ⇒ flat).
3. `risk.py` gate: caps, daily-loss halt, market-open, kill switch.
4. Reconcile: stance says enter + no position + within rails ⇒ place order (demo first). Price hit `invalidation` ⇒ close. Stance flipped ⇒ flatten/reverse.
5. Append decision row to SQLite — hash each row (chain-friendly, fits your audit instinct).
6. Telegram heartbeat: equity, open P&L, positions, last action, next-analysis ETA.

The daemon **never calls the LLM.** It only reads `Stance` + live data and acts.

### 4.2 Brain (Claude Code scheduled task / Routine, Mode A, slow cadence)
Defined once in `brain/CLAUDE.md` + `brain/analyze.md`. On each fire (hourly / on-signal):
1. Pull market context: recent OHLCV + indicators (cTrader MCP), news/sentiment (TradingAgents data tools).
2. Run the TradingAgents reasoning flow — Analysts → Bull/Bear debate → Trader → Risk → Portfolio Manager — **as prompts Claude executes itself** (this is Mode A; no `.propagate()` SDK call, no API key).
3. Emit a `Stance` per instrument via `write_stance.py` → Stance bus.
4. Post a one-paragraph summary to Telegram.

> Cadence math: keep brain runs to ~1–24/day so they stay inside subscription limits. Never point a Routine at the 5-min tick.

### 4.3 The Stance bus
Co-located host ⇒ shared local **SQLite file** (simplest). Split host (daemon on VPS, brain as Cloud Routine) ⇒ a store both reach: **Google Drive** (you have it connected), a tiny key-value endpoint, or a **git commit** the daemon pulls.

---

## 5. Risk guardrails (`risk.py`, non-negotiable)
- `HOST=demo` default; live requires explicit env + one-time confirm.
- Max lots, max concurrent positions, max daily loss ⇒ auto-flatten + halt.
- Mandatory per-trade stop-loss (MCP/bot supports SL/TP natively).
- **Kill switch:** Telegram `/halt` *and* a sentinel file both stop new orders.
- Stance TTL enforced: expired stance = no action.
- Only the daemon executes; the brain can never place an order directly.

---

## 6. Deployment — pick your host (this picks brain-trigger + bus)

| Host | Brain trigger | Stance bus | Notes |
|---|---|---|---|
| **Always-on Mac/Windows box** (co-located) | **Desktop scheduled task** (macOS/Windows only) | local SQLite | Simplest. Daemon + Claude Code on one machine, shared files. Machine must stay on. |
| **Linux VPS** (co-located) | **cron + `claude -p`** headless | local SQLite | Desktop tasks aren't on Linux; use headless. Daemon + headless brain share the box. |
| **VPS daemon + laptop-off brain** (split) | **Cloud Routine** (Anthropic infra) | Drive / KV / git | Brain runs even with your machine off; needs a remote bus + outbound TCP to cTrader from the daemon host. |

cTrader needs outbound TCP (5035 demo / 5034 live) wherever the **daemon** runs — another reason cTrader execution lives in the daemon on a host you control, not in a Routine sandbox.

**Recommended start:** co-located on one always-on host (VPS if you want laptop-off; Mac/Win if you prefer Desktop tasks), local SQLite bus. Add the split/Cloud-Routine path later only if you need the laptop fully off.

---

## 7. Phased build plan

**Phase 0 — Fork & boot.** Monorepo; both repos in (licenses preserved). `mcp/ctrader` authenticating to a **demo** account; `test_server.py` green. Confirm TradingAgents reasoning runs in your chosen Claude Code surface.

**Phase 1 — Daemon vertical slice (no trading).** Build `ctrader_client.py` (Option 1 import), `state.py`, `telegram.py`. `heartbeat.py` does snapshot + Telegram only ⇒ prove 5-min heartbeat with real demo-account data.

**Phase 2 — Brain + Stance bus (no trading).** Write `brain/CLAUDE.md` + `analyze.md` + `write_stance.py`. Stand up the chosen Routine; it writes stances; daemon reads + Telegram-summarizes them. Still no orders.

**Phase 3 — Execution under rails (demo).** Add `risk.py` + reconcile step. Place/close orders on **demo** only. Validate fills, SL/TP, kill switch, daily-loss halt.

**Phase 4 — Cloud + hardening.** Containerize the daemon, supervised restart, secrets, log rotation, decision-row hashing, alert on heartbeat-miss and on stale-stance. Tune brain cadence to stay within usage limits.

**Phase 5 — Live (gated).** Only after a long demo soak: `HOST=live`, smaller caps, manual confirm gate on first live orders.

---

## 8. Secrets & config (`.env`)
```
# cTrader
CLIENT_ID= / CLIENT_SECRET= / ACCESS_TOKEN= / ACCOUNT_ID=
HOST=demo                      # demo until proven
# Telegram
TELEGRAM_BOT_TOKEN= / TELEGRAM_CHAT_ID=
# Daemon / risk
HEARTBEAT_SECONDS=300
WATCHLIST=EURUSD,GBPUSD,XAUUSD
MAX_LOTS= / MAX_POSITIONS= / MAX_DAILY_LOSS=
# Stance bus
STANCE_STORE=sqlite            # sqlite | drive | git | kv
STANCE_DB_PATH=./algo-trader-bot.db
# Brain cadence (set in the Routine/cron, not here): e.g. 0 * * * *
```
No `ANTHROPIC_API_KEY` — Mode A uses your subscription via Claude Code. (Keep an optional API-key path only as a validation fallback if you ever want headless `.propagate()`.)

---

## 9. Honest gaps / confirm before coding
1. **Timeframe + asset semantics (biggest real risk).** TradingAgents reasons on tickers + dates with daily news/fundamentals; cTrader is intraday FX/CFD. Define what "analyze EURUSD" means and which TradingAgents data tools even cover FX — several are equities-oriented. This is harder than the plumbing.
2. **cTrader token lifetime.** Access tokens expire — add refresh handling in `ctrader_client.py`.
3. **Consume the decision, not the executor.** TradingAgents assumes a simulated exchange + portfolio-manager approval. Wire only its *decision* into `Stance`; never let it execute. Real execution = daemon + `risk.py`.
4. **Usage-limit budget.** Each brain run is a full Claude Code session against your plan. Pick cadence accordingly; watch for limit exhaustion silently starving the brain (alert on stale stance).
5. **Live trading is a separate, gated milestone.** Everything stays demo until soak-tested.

---

## 10. First commit checklist
- [ ] Monorepo created; both repos forked in; MIT + Apache-2.0 preserved
- [ ] Demo cTrader auth working; `test_server.py` green
- [ ] `daemon/ctrader_client.py` imports `ctrader_bot` directly and returns a live snapshot
- [ ] Heartbeat posts real account data to Telegram every 5 min (no trading)
- [ ] `Stance` dataclass + `stance_store` (sqlite) implemented
- [ ] `brain/CLAUDE.md` + `analyze.md` defined; one Routine run writes a Stance
- [ ] `risk.py` kill switch + demo gate in place **before** any order code
