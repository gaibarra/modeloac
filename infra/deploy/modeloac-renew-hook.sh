#!/usr/bin/env bash
set -euo pipefail
if [[ "${RENEWED_LINEAGE:-}" != '/etc/letsencrypt/live/modeloac.online' ]]; then
    exit 0
fi
/usr/sbin/nginx -t
/usr/bin/systemctl reload nginx
