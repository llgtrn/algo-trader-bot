"""Brain executor — runs TradingAgents' real graph and emits a Stance.

This is the wired ``.propagate()`` path (the user's chosen brain mode). It loads
the TradingAgents graph, runs the full Analysts → Bull/Bear → Trader → Risk →
Portfolio-Manager flow for one instrument, maps the resulting rating to a
``Stance``, and writes it to the bus for the daemon to consume.

Requires an API key for the configured provider, e.g.:
    TRADINGAGENTS_LLM_PROVIDER=anthropic
    ANTHROPIC_API_KEY=sk-ant-...

Usage:
    python -m brain.run_analysis EURUSD [YYYY-MM-DD]

Cadence: run this on a SLOW schedule (1–24×/day). Never point it at the 5-min
heartbeat — each run is a full reasoning pass (blueprint §4.2).
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# Make the vendored TradingAgents package importable (package-root on path).
_TA_ROOT = Path(__file__).resolve().parent.parent / "agents" / "tradingagents"
if str(_TA_ROOT) not in sys.path:
    sys.path.insert(0, str(_TA_ROOT))

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from daemon.config import load_settings  # noqa: E402
from brain import write_stance as ws  # noqa: E402


def run(instrument: str, trade_date: str | None = None) -> object:
    """Run the reasoning graph for one instrument and emit a Stance."""
    trade_date = trade_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    settings = load_settings()

    # Imported lazily so `python -m brain.run_analysis` fails clearly with a
    # missing-dependency message rather than at module import time.
    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.graph.trading_graph import TradingAgentsGraph

    config = dict(DEFAULT_CONFIG)  # env (TRADINGAGENTS_*) overrides apply inside

    graph = TradingAgentsGraph(config=config)
    final_state, rating = graph.propagate(instrument, trade_date)

    stance = ws.build_stance(instrument, rating, final_state)
    ws.emit_stance(settings.stance_db_path, stance)
    print(
        f"Stance emitted: {stance.instrument} {stance.direction} "
        f"(conv {stance.conviction:.2f}, target={stance.target}, "
        f"invalidation={stance.invalidation}) → {settings.stance_db_path}"
    )
    return stance


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: python -m brain.run_analysis INSTRUMENT [YYYY-MM-DD]")
        return 2
    instrument = argv[0]
    trade_date = argv[1] if len(argv) > 1 else None
    run(instrument, trade_date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
