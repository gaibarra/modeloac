#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
umask 077
mkdir -p backups
backup_path="backups/modeloac-$(date -u +%Y%m%dT%H%M%SZ).dump"
docker compose --env-file .env.production -f compose.production.yml exec -T db pg_dump -U modeloac -d modeloac -Fc > "$backup_path"
test -s "$backup_path"
printf 'Respaldo creado: %s\n' "$backup_path"
