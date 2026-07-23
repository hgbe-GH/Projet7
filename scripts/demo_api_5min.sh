#!/usr/bin/env bash
set -euo pipefail

python scripts/demo_api_5min.py --ensure-compose "$@"
