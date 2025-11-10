#!/usr/bin/env bash
# Simple launcher to run scraper_gui.py; prefers .venv python if present
BASEDIR="$(cd "$(dirname "$0")" && pwd)"
# prefer project's virtualenv
PY="$BASEDIR/.venv/bin/python"
if [ ! -x "$PY" ]; then
  # fallback to system python
  PY="$(command -v python3 || command -v python)"
fi
# execute the GUI script from project dir
exec "$PY" "$BASEDIR/scraper_gui.py" "$@"
