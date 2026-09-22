# Despliegue aislado de Modelo AC

## Estado actual

Vista previa local: frontend `127.0.0.1:3108`, Gunicorn `127.0.0.1:8188`, PostgreSQL exclusivo en `127.0.0.1:5548`. Servicios transitorios de usuario `modeloac-preview-frontend` y `modeloac-preview-backend`. Base de desarrollo en el proyecto Compose **modeloac-dev**, con volumen propio.

No se ha instalado el sitio Nginx ni emitido certificado. Dominio pendiente de confirmación. Las plantillas de esta carpeta no se activan por sí solas.

Para acceder desde otro equipo mientras no hay dominio:

```bash
ssh -L 3108:127.0.0.1:3108 gaibarra@IP_DEL_SERVIDOR
```

Abrir `http://localhost:3108`. La cuenta inicial está en `.work/acceso-inicial.json` (permisos 600). Cambiar la contraseña en `/admin/password_change/` al entrar. No subir ese archivo a control de versiones.

## Producción

1. Inventariar puertos, unidades, sitios Nginx y contenedores. Los puertos 3108 y 8188 están reservados para esta app; confirmar que pertenecen a sus vistas previas antes de detenerlas. No detener servicios ajenos.
2. Preparar `.env.production` con permisos 600: clave Django única, `DJANGO_DEBUG=0`, `POSTGRES_PASSWORD` aleatoria, `DATABASE_URL=postgresql://modeloac:CLAVE@db:5432/modeloac`, `DJANGO_ALLOWED_HOSTS=DOMINIO,localhost,127.0.0.1,backend`, `CSRF_TRUSTED_ORIGINS=https://DOMINIO`, `HTTPS_ENABLED=1`. No usar la clave de ejemplo. No publicar el acceso con contraseñas sobre HTTP.
3. Construir antes de detener la vista previa:

   ```bash
   docker compose --env-file .env.production -f compose.production.yml build
   docker compose --env-file .env.production -f compose.production.yml up -d db
   ```

4. Si ya hay datos operativos en producción, ejecutar `scripts/backup.sh` y comprobar el respaldo antes de cada migración. La base de producción es independiente: para conservar cambios capturados en vista previa, respaldar **modeloac-dev** con `pg_dump -Fc` y restaurar explícitamente en la base nueva vacía. No importar de nuevo como sustituto de una restauración de datos operativos.
5. Aplicar migraciones y roles:

   ```bash
   docker compose --env-file .env.production -f compose.production.yml run --rm backend python manage.py migrate
   docker compose --env-file .env.production -f compose.production.yml run --rm backend python manage.py setup_roles
   ```

6. Si es una instalación nueva sin restauración, importar `/app/data/initial_inventory.json` con `python manage.py import_inventory /app/data/initial_inventory.json`, primero con `--dry-run`. Crear administrador mediante `python manage.py createsuperuser`. No hay usuario ni contraseña predeterminados dentro de las imágenes.
7. Detener exclusivamente las vistas previas de esta aplicación:

   ```bash
   systemctl --user stop modeloac-preview-frontend modeloac-preview-backend
   ```

8. Instalar `infra/modeloac.service` como `/etc/systemd/system/modeloac.service`, ejecutar `systemctl daemon-reload` y `systemctl enable --now modeloac`. La unidad solo administra el proyecto **modeloac-prod**, sin `down -v`, sin limpieza de Docker y sin migraciones automáticas.
9. Confirmar DNS y copiar la plantilla Nginx sustituyendo únicamente `DOMINIO_PENDIENTE`, a `/etc/nginx/sites-available/modeloac.conf`. Crear su enlace exclusivo en `sites-enabled`. No cambiar otros sitios ni el sitio por defecto. Verificar con `nginx -t`; recargar solo si es válido. Comprobar antes y después la respuesta de las otras aplicaciones.
10. HTTPS cuando se confirme el dominio: `certbot --nginx -d DOMINIO`, limitado al sitio de Modelo AC. Revisar los cambios de ese archivo y comprobar certificado, redirección HTTP→HTTPS, renovación, login y cookies seguras. No solicitar certificados de otros dominios.

## Verificación y operación

- `docker compose --env-file .env.production -f compose.production.yml ps`
- `curl http://127.0.0.1:8188/api/health/`
- `curl -I http://127.0.0.1:3108/`
- `docker compose --env-file .env.production -f compose.production.yml run --rm backend python manage.py check --deploy`
- Entrar, filtrar equipos, registrar una orden de prueba acordada, descargar PDF/Excel y comprobar roles.
- Programar respaldos exclusivos de `modeloac` según la retención institucional. Probar restauración en una base temporal separada; comprobar que el archivo no solo existe, sino que es recuperable.

La tasa de intentos de login se limita en Django por IP y proceso. La plantilla añade además una zona Nginx exclusiva `modeloac_login`, sin modificar las de otros sitios. HTTPS activa redirección y cookies seguras; el endpoint de salud local está exento de redirección para permitir supervisión. No se han añadido tareas programadas ni servicios Redis/Celery: la agenda se consulta directamente y los reportes son síncronos.

## Reversión

Ante un fallo de la aplicación, revertir solo sus imágenes/versiones y su archivo de sitio. No revertir bases con nuevas capturas sin respaldo y revisión. Nunca borrar volúmenes. Un fallo de `nginx -t` impide recargar. Mantener las otras aplicaciones intactas es un criterio de aceptación del despliegue.
