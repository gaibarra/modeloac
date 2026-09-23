# Despliegue de modeloac.online

Estado: publicado y verificado el 22 de septiembre de 2026, 23:40 UTC, en https://modeloac.online. Los tres contenedores están saludables; la renovación de prueba y las comprobaciones HTTPS, autenticación, CSRF, permisos y exportaciones finalizaron correctamente.

```bash
sudo /home/gaibarra/modeloac/scripts/deploy-production.sh
```

El instalador respalda Nginx, emite el certificado con webroot y la cuenta ACME existente, prueba la renovación únicamente de modeloac.online, detiene las dos vistas previas, respalda PostgreSQL y restaura en el volumen exclusivo modeloac-prod_modeloac_db. Compara conteos y hashes de todas las tablas Django, incluidas cuentas y relaciones, antes de migrar. No importa nuevamente el PDF. Activa systemd, publica HTTPS y valida permisos, CSRF, sesiones, fuentes y exportaciones. La nueva clave Django requiere iniciar sesión otra vez.

Next.js escucha en 127.0.0.1:3108 y Gunicorn en 127.0.0.1:8188. PostgreSQL no publica puertos. Se instala únicamente el sitio modeloac.conf; cada recarga pasa nginx -t. www redirige al dominio principal conservando ruta y parámetros. Los secretos están en .env.production con permisos 600.

Los respaldos privados diarios se ejecutan a las 03:15 America/Mexico_City. Solo se eliminan copias modeloac-prod-*.dump con antigüedad mayor al límite de 14 días después de verificar una nueva. El respaldo inicial y los de transferencia se conservan. Esta copia local no sustituye un respaldo externo.

Si falla una comprobación, el dominio queda en mantenimiento. Antes de publicar se intenta reanudar únicamente las vistas previas. Si producción pudo recibir cambios, no se reactiva la base anterior: se conserva un respaldo de producción y se exige conciliación. Nunca se eliminan volúmenes. Las marcas en .work/deploy impiden sobrescribir una base restaurada o repetir automáticamente una publicación incompleta. No borrar estas marcas para forzar un reintento.

Validación previa: imágenes construidas; restauración de un respaldo nuevo en base temporal aislada; 14 pruebas Django aprobadas (HTTPS_ENABLED=0 solo para el cliente HTTP interno de pruebas); configuración de seguridad de producción comprobada; tres configuraciones Nginx comprobadas con certificados temporales y puertos de prueba. Las advertencias Django sobre HSTS en subdominios y preload corresponden a exclusiones deliberadas del plan. Las verificaciones HTTPS públicas y la renovación de prueba finalizaron correctamente durante el instalador.

Se registraron 14 respuestas HTTP/HTTPS de otros sitios y hashes de sus configuraciones. educomply.online y modeloxml.online ya respondían 502 antes de este despliegue; se conservó esa referencia sin intervenir dichas aplicaciones.

Evidencias privadas: .work/deploy y backups. La transferencia definitiva se completó con comparación de conteos y hashes. Las vistas previas quedaron detenidas; se conservan su base y los respaldos. El primer respaldo de producción se verificó correctamente; el siguiente está programado para el 23 de septiembre de 2026 a las 03:15 America/Mexico_City.
