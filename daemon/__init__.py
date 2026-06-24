"""algo-trader-bot daemon — the 24/7 muscle.

Plain Python, no LLM. Reads live cTrader data + the latest Stance from the bus
and (in later phases) executes within risk rails. This Phase-1 build is
snapshot-only: it reports a heartbeat to Telegram and never places orders.
"""
