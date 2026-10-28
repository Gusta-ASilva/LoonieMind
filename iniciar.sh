#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
if [ ! -f .venv/bin/python ]; then
  python3.12 -m venv .venv
  .venv/bin/python -m pip install -r requirements-lock.txt
fi
exec .venv/bin/python run.py
