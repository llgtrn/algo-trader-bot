# Daemon container — the 24/7 muscle (no LLM).
# Build context is the repo root: docker build -f deploy/Dockerfile .
FROM python:3.11-slim

WORKDIR /app

# System deps kept minimal; Twisted + ctrader-open-api are pure-Python wheels.
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install daemon deps first for layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the daemon and the vendored cTrader core it imports directly.
# (The brain / TradingAgents is run separately on a scheduler, not in this
# always-on container.)
COPY daemon/ ./daemon/
COPY mcp/ ./mcp/

# The SQLite stance bus lives on a mounted volume (see docker-compose.yml).
VOLUME ["/data"]
ENV STANCE_DB_PATH=/data/algo-trader-bot.db \
    KILL_SWITCH_FILE=/data/HALT

CMD ["python", "-m", "daemon.heartbeat"]
