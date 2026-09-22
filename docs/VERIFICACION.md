# Entrega verificada · 22 de septiembre de 2026

## Resultado

Versión funcional local de Modelo AC en `/home/gaibarra/modeloac`. Datos reales, sin registros ficticios. Frontend Next.js/TypeScript, API Django REST Framework, Gunicorn y PostgreSQL aislado.

## Comprobaciones ejecutadas

- Django `check`: sin incidencias.
- 14 pruebas backend aprobadas: autenticación, CSRF, permisos por rol, duplicados, costos/fechas, cierre preventivo, contraseña, checklist, reportes y reimportación que preserva equipos renombrados.
- Reimportación real: 0 ubicaciones, 0 modelos, 0 equipos y 0 históricos adicionales.
- Migraciones: sin cambios pendientes de generar.
- `next build --webpack`: compilación y TypeScript aprobados.
- Chromium/Playwright: login, tablero, inventario de 318 componentes, búsqueda de ubicación dudosa, catálogos de formularios, fuentes autenticadas, descarga Excel, módulos, vista móvil de 390 px sin desbordamiento horizontal y cierre de sesión. Sin errores JavaScript.
- Capturas de escritorio y móvil inspeccionadas en `docs/screenshots/`.
- Imágenes `modeloac-prod-backend` y `modeloac-prod-frontend` construidas correctamente, incluyendo build Next.js dentro de Docker.
- Configuración Compose validada con variables ficticias. Scripts shell verificados sintácticamente.
- Auditoría npm de dependencias de producción: 0 vulnerabilidades reportadas al momento de la ejecución.
- `/api/health/` a través del frontend devuelve `status: ok`.
- Servicios y contenedores de las aplicaciones existentes revisados: siguen activos. No se editaron sus configuraciones ni se reiniciaron sus servicios.

## Estado persistido

318 componentes, 134 ubicaciones, 37 modelos y 90 trabajos históricos. 70 revisiones de fuente incluyen nomenclaturas técnicas, ubicaciones/modelos desconocidos, 11 posibles repeticiones, cuatro solicitudes históricas, páginas de evidencia y una fila tachada. Los 318 estados físicos y sus fechas de próximo mantenimiento requieren captura/verificación en campo.

Respaldo inicial: `backups/modeloac-inicial-20260922.dump`, formato PostgreSQL custom, permisos 600. Es un respaldo creado; todavía no se ha ensayado una restauración operativa con él.

## Pendiente de publicación

No se instaló la unidad de producción ni el sitio Nginx; no se emitió certificado. La vista previa utiliza unidades transitorias de usuario y puertos de loopback 3108/8188/5548. Puede requerir volver a iniciarse tras reiniciar el servidor. El procedimiento persistente está preparado en `docs/DESPLIEGUE.md`.

Con `HTTPS_ENABLED=1`, Django activa cookies seguras, HSTS y redirección HTTPS. `check --deploy` mantiene únicamente advertencias sobre HSTS para subdominios y preload; se dejaron desactivados intencionalmente hasta conocer el dominio y el alcance sobre otros sitios. La vista previa local usa HTTP con `HTTPS_ENABLED=0` y no se expone públicamente.

Los reportes financieros nuevos usan MXN. Los costos históricos permanecen literales y separados porque la fuente no declara moneda ni el significado de los ceros. La recepción de compras exige registrar físicamente sus componentes; no los genera automáticamente. Manuales por URL, sin carga de adjuntos en esta versión.
