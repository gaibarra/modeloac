# Modelo AC — Guía de operación

## Roles y acceso

- **Administración:** captura y modifica inventario, modelos, ubicaciones, proveedores, adquisiciones y órdenes; resuelve revisiones.
- **Mantenimiento:** consulta la información y crea/actualiza órdenes de trabajo. No cambia compras ni inventario.
- **Consulta:** lectura y exportación.
- Un superusuario puede administrar cuentas desde **Mi cuenta → Administrar usuarios**. Asignar un único grupo por usuario. Las contraseñas no se incluyen en la aplicación ni en imágenes de contenedor.

Haz clic en tu nombre al pie del menú para cambiar tu contraseña. El nombre de usuario inicial es `administrador`; su clave aleatoria está en `.work/acceso-inicial.json`, únicamente en este servidor. Después de cambiarla, ese archivo deja de ser una credencial vigente.

## Inventario

Buscar por código, marca, modelo o ubicación. Abrir la ficha desde el código o la flecha. **Editar registro** permite completar número de serie, estado, adquisición, garantía, costos e intervalo preventivo. La ficha incluye las intervenciones nuevas y el histórico original asociado.

Los códigos del catálogo original se conservan. No asumir que una evaporadora y una condensadora son duplicados: son dos componentes. Antes de declarar un sistema operativo, revisar ambos y sus datos físicos. No hay borrado desde la interfaz; marcar equipos retirados como **Baja** conserva su historia.

## Modelos y ubicaciones

La biblioteca técnica centraliza datos de placa, capacidad, inverter, refrigerante, voltaje, potencia y URL del manual. Un cambio de modelo se refleja en sus componentes vinculados. Los modelos importados necesitan cotejo con sus placas. Las ubicaciones respetan las claves originales y se buscarán por código, edificio o nombre.

## Mantenimiento

1. Abrir **Mantenimiento → Nueva orden de trabajo**.
2. Elegir el componente, concepto, tipo, prioridad, fecha y responsable.
3. Documentar diagnóstico y lista de revisión; pasar a **En proceso** cuando corresponda.
4. Registrar el trabajo realizado, fecha real de terminación y costo conocido.
5. Cerrar como **Completada**. En un preventivo, la próxima fecha se calcula con el intervalo del equipo. Esto no declara el equipo operativo automáticamente: verificar su estado en Inventario.

Una orden cerrada conserva su historial y no se modifica. Para correcciones o trabajos adicionales, crear otra orden con referencia a la anterior. Una fecha histórica no retrocede una programación posterior existente. La agenda muestra órdenes por mes, incluidas canceladas y completadas con su estado.

## Adquisiciones

Registrar solicitud, modelo, destino, cantidad de sistemas, precio unitario, proveedor, justificación y fecha prevista. Avanzar por Solicitada, Aprobada, En compra y Recibida; se puede cancelar. Al recibir, registrar los componentes con códigos únicos en Inventario y anotar la referencia de compra. La recepción no genera componentes automáticamente porque su cantidad y composición requieren identificación física. Registrar factura, costo, fecha y garantía conocidos.

## Reportes

Exportaciones CSV, Excel y PDF de inventario, próximos mantenimientos, órdenes/costos, adquisiciones, garantías, calidad e histórico original. Las fechas filtran órdenes; el edificio filtra reportes de equipos. Los filtros no aplicables se explican en pantalla. El histórico original conserva costos literales y no se mezcla con costos nuevos en MXN.

La simulación energética utiliza `kW × horas/día × días × tarifa`. Introducir potencia real o nominal documentada; no convertir automáticamente BTU/h a consumo eléctrico. Es una estimación, no una medición ni una factura.

## Calidad y trazabilidad

Revisión de datos muestra el documento original autenticado y la transcripción. Corregir primero la ficha operativa y después documentar la verificación. Las solicitudes antiguas y los posibles trabajos repetidos se conservan para revisión. La bitácora registra usuario, fecha, campos anteriores y nuevos de las modificaciones realizadas por API. Los cambios de cuentas realizados por Django Admin tienen su propia bitácora del administrador.

Los botones de impresión usan el diálogo de impresión del navegador. Para compartir listados formateados, usar PDF desde Reportes.

## Consulta completa de mantenimiento

En **Mantenimiento** se consultan juntos los trabajos del histórico importado y las órdenes creadas en la aplicación, ordenados por fecha descendente. Usa **Realizados** para ver tanto intervenciones históricas como órdenes completadas; el filtro **Origen** permite separarlas. La búsqueda incluye equipo, ubicación, trabajo, referencia y técnico.

Cada fila indica su origen. Los históricos mantienen su referencia original, fecha y posibles repeticiones; su ficha es de consulta y conserva los costos literales sin asumir moneda. No se duplican como órdenes nuevas ni modifican la agenda. **Nueva orden de trabajo** continúa disponible para los roles autorizados.
