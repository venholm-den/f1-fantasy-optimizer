#!/usr/bin/env bash
set -euo pipefail

SEASON="${1:-2025}"

cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip -q install -U pip
pip -q install requests

python -m src.scrape_f1fantasytools --season "$SEASON"
python -m src.dimensions --season "$SEASON"
python -m src.ergast_schedule --season "$SEASON"

echo "Done: refreshed season $SEASON"
