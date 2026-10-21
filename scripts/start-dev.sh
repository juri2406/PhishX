#!/usr/bin/env bash
# One foreground process group; Ctrl+C stops both children started here.
set -euo pipefail
cd "$(dirname "$0")/.."
exec .venv/bin/python scripts/start_dev.py "$@"
