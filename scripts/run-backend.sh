#!/usr/bin/env bash
set -euo pipefail
cd /home/gaibarra/modeloac
set -a
source .env
set +a
exec .venv/bin/gunicorn --chdir backend config.wsgi:application --no-control-socket --bind 127.0.0.1:8188 --workers 2 --timeout 90 --access-logfile - --error-logfile -
