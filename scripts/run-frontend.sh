#!/usr/bin/env bash
set -euo pipefail
cd /home/gaibarra/modeloac
set -a
source .env
set +a
exec npm run start --prefix frontend
