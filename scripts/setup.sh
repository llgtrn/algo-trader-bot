#!/usr/bin/env bash
# No-Docker setup for algo-trader-bot.
# Creates a venv, installs deps, and copies the env template.
#
#   bash scripts/setup.sh
#
# Windows (PowerShell): run the equivalent steps —
#   python -m venv .venv; .venv\Scripts\activate; pip install -r requirements.txt
#   copy deploy\.env.example .env
set -euo pipefail

cd "$(dirname "$0")/.."

python -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp deploy/.env.example .env
  echo "Created .env from template — fill in CLIENT_ID/CLIENT_SECRET/ACCESS_TOKEN/"
  echo "REFRESH_TOKEN/ACCOUNT_ID (HOST=demo)."
fi

echo
echo "Setup complete. Next:"
echo "  1) edit .env with your cTrader credentials"
echo "  2) python scripts/refresh_token.py     # optional: mint a fresh token now"
echo "  3) attach the MCP in Claude Code (see .mcp.json) OR run the daemon:"
echo "       python -m daemon.heartbeat"
