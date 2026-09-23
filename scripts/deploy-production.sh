#!/usr/bin/env bash
# Ejecutar como root. Solo administra Modelo AC; no instala ni actualiza paquetes.
set -Eeuo pipefail
umask 077
app_dir=/home/gaibarra/modeloac
cd "$app_dir"
if [[ $EUID -ne 0 ]]; then
    echo 'Este paso requiere sudo/root para Nginx, Certbot y systemd. No se ha modificado el servidor.' >&2
    exit 77
fi
compose=(docker compose --env-file "$app_dir/.env.production" -f "$app_dir/compose.production.yml")
dev=(docker compose --env-file "$app_dir/.env" -f "$app_dir/compose.db.yml")
state="$app_dir/.work/deploy"
site=/etc/nginx/sites-available/modeloac.conf
link=/etc/nginx/sites-enabled/modeloac.conf
app_uid=$(id -u gaibarra)
as_app() { runuser -u gaibarra -- env XDG_RUNTIME_DIR="/run/user/$app_uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$app_uid/bus" "$@"; }
if [[ -f "$state/published.ok" ]]; then
    python3 scripts/verify-production.py
    python3 scripts/verify-other-sites.py
    echo 'Modelo AC ya está publicado y verificado.'
    exit 0
fi
if [[ -f "$state/publication-started" ]]; then
    echo 'Una publicación anterior requiere conciliación/verificación manual; no se tocarán datos ni vistas previas.' >&2
    exit 1
fi
if [[ ( -e "$site" || -L "$link" ) && ! -f "$state/site-owned" ]]; then
    echo 'Existe configuración modeloac ajena a esta ejecución. Revisar antes de continuar.' >&2
    exit 1
fi
nginx -t
python3 scripts/verify-other-sites.py
"${compose[@]}" config --quiet
"${compose[@]}" build
run_dir="$app_dir/backups/deploy-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$run_dir"
chmod 700 "$run_dir"
tar -czf "$run_dir/nginx-before.tar.gz" -C /etc nginx
"${compose[@]}" images --format json > "$run_dir/images.json"
docker image inspect modeloac-prod-backend modeloac-prod-frontend --format '{{.RepoTags}} {{.Id}}' > "$run_dir/application-images.txt"
nginx_changed=0
published=0
frozen=0
failure() {
    local code=$?
    trap - ERR
    if (( nginx_changed )); then
        if [[ -f /etc/letsencrypt/live/modeloac.online/fullchain.pem ]]; then
            install -m 644 infra/deploy/nginx-maintenance.conf "$site"
        else
            install -m 644 infra/deploy/nginx-bootstrap.conf "$site"
        fi
        if nginx -t; then systemctl reload nginx; fi
    fi
    echo "Despliegue no aceptado (error $code). Respaldos en $run_dir; no se borró ningún volumen." >&2
    if (( published )); then
        echo 'Pudo haber capturas en producción: no reactivar la base anterior sin conciliación.' >&2
        "${compose[@]}" exec -T db pg_dump -U modeloac -d modeloac -Fc > "$run_dir/production-on-failure.dump" || true
    elif (( frozen )); then
        systemctl stop modeloac.service || true
        "${compose[@]}" stop frontend backend || true
        for component in backend frontend; do
            as_app systemctl --user start "modeloac-preview-$component" || as_app systemd-run --user --unit="modeloac-preview-$component" --property=Restart=on-failure "$app_dir/scripts/run-$component.sh" || true
        done
        echo 'Se intentó reactivar únicamente la vista previa de Modelo AC.' >&2
    fi
    exit "$code"
}
trap failure ERR
install -d -m 755 /var/www/modeloac-acme/.well-known/acme-challenge
install -m 644 infra/deploy/nginx-bootstrap.conf "$site"
if [[ ! -L "$link" ]]; then ln -s "$site" "$link"; fi
touch "$state/site-owned"
nginx_changed=1
nginx -t
systemctl reload nginx
python3 scripts/verify-other-sites.py
acme_account=$(awk -F ' = ' '$1 == "account" {print $2}' /etc/letsencrypt/renewal/asistenciamodelo.online.conf)
[[ "$acme_account" =~ ^[a-f0-9]{32}$ ]]
certbot certonly --non-interactive --webroot -w /var/www/modeloac-acme --cert-name modeloac.online --account "$acme_account" -d modeloac.online -d www.modeloac.online
install -d -m 755 /etc/letsencrypt/renewal-hooks/deploy
install -m 755 infra/deploy/modeloac-renew-hook.sh /etc/letsencrypt/renewal-hooks/deploy/modeloac-reload
certbot renew --cert-name modeloac.online --dry-run --non-interactive
"${compose[@]}" up -d --wait db
if [[ ! -f "$state/restored.ok" ]]; then
    table_count=$("${compose[@]}" exec -T db psql -U modeloac -d modeloac -Atc "SELECT count(*) FROM pg_tables WHERE schemaname='public'")
    [[ "$table_count" == 0 ]] || { echo 'La base de producción ya contiene tablas: no se sobrescribirá.' >&2; false; }
    as_app systemctl --user stop modeloac-preview-frontend modeloac-preview-backend
    frozen=1
    as_app bash -c 'cd /home/gaibarra/modeloac; set -a; source .env; set +a; .venv/bin/python backend/manage.py deployment_fingerprint' > "$state/source-fingerprint.json"
    "${dev[@]}" exec -T db pg_dump -U modeloac -d modeloac -Fc > "$run_dir/transfer.dump"
    test -s "$run_dir/transfer.dump"
    "${compose[@]}" exec -T db pg_restore --list < "$run_dir/transfer.dump" > /dev/null
    "${compose[@]}" exec -T db pg_restore -U modeloac -d modeloac --single-transaction --exit-on-error --no-owner --no-privileges < "$run_dir/transfer.dump"
    "${compose[@]}" run --rm -T --no-deps backend python manage.py deployment_fingerprint > "$state/production-fingerprint.json"
    cmp "$state/source-fingerprint.json" "$state/production-fingerprint.json"
    touch "$state/restored.ok"
else
    # No continuar con una copia vieja si la vista previa recibió cambios.
    as_app bash -c 'cd /home/gaibarra/modeloac; set -a; source .env; set +a; .venv/bin/python backend/manage.py deployment_fingerprint' > "$state/current-source-fingerprint.json"
    cmp "$state/source-fingerprint.json" "$state/current-source-fingerprint.json"
    # Una ejecución previa pudo restaurar: nunca sobrescribir esa base.
    as_app systemctl --user stop modeloac-preview-frontend modeloac-preview-backend
    frozen=1
    "${compose[@]}" run --rm -T --no-deps backend python manage.py deployment_fingerprint > "$state/production-fingerprint.json"
    cmp "$state/source-fingerprint.json" "$state/production-fingerprint.json"
fi
"${compose[@]}" run --rm -T --no-deps backend python manage.py migrate --noinput
"${compose[@]}" run --rm -T --no-deps backend python manage.py check --deploy
install -m 644 infra/modeloac.service /etc/systemd/system/modeloac.service
install -m 644 infra/modeloac-backup.service /etc/systemd/system/modeloac-backup.service
install -m 644 infra/modeloac-backup.timer /etc/systemd/system/modeloac-backup.timer
systemctl daemon-reload
systemctl enable --now modeloac.service
"${compose[@]}" up -d --wait --wait-timeout 120 --no-build
curl --retry 10 --retry-connrefused --retry-delay 2 --max-time 15 --fail --silent --show-error http://127.0.0.1:8188/api/health/ > /dev/null
curl --retry 10 --retry-connrefused --retry-delay 2 --max-time 15 --fail --silent --show-error http://127.0.0.1:3108/ > /dev/null
install -m 644 infra/deploy/nginx-production.conf "$site"
nginx -t
touch "$state/publication-started"
published=1
systemctl reload nginx
python3 scripts/verify-production.py
python3 scripts/verify-other-sites.py
systemctl enable --now modeloac-backup.timer
systemctl start modeloac-backup.service
systemctl is-active modeloac.service modeloac-backup.timer certbot.timer
"${compose[@]}" ps
printf '%s\n' "https://modeloac.online publicado y verificado el $(date -u +%FT%TZ)" > "$state/published.ok"
chown gaibarra:gaibarra "$state/published.ok"
trap - ERR
echo 'Publicación terminada: https://modeloac.online (www redirige al dominio principal).'
