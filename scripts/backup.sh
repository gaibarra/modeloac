#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
umask 077
mkdir -p backups
backup_path="backups/modeloac-prod-$(date -u +%Y%m%dT%H%M%SZ).dump"
temporary_path="${backup_path}.partial"
trap 'rm -f -- "$temporary_path"' EXIT
docker compose --env-file .env.production -f compose.production.yml exec -T db pg_dump -U modeloac -d modeloac -Fc > "$temporary_path"
test -s "$temporary_path"
docker compose --env-file .env.production -f compose.production.yml exec -T db pg_restore --list < "$temporary_path" > /dev/null
mv -- "$temporary_path" "$backup_path"
# Solo respaldos de produccion de esta aplicacion; no toca el respaldo inicial.
find "$PWD/backups" -maxdepth 1 -type f -name 'modeloac-prod-*.dump' -mtime +14 -delete
printf 'Respaldo verificado: %s\n' "$backup_path"
