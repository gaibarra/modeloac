# Conciliación del inventario de origen

Fuentes: `DOCUMENTOS.pdf` (13 páginas) y `WhatsApp Image 2026-09-22 at 14.01.07.jpeg`. Sus hashes SHA-256 se guardan en `data/initial_inventory.json`.

| Fuente | Contenido | Tratamiento |
| --- | --- | --- |
| PDF páginas 4–9 | 318 filas de equipos | Se conservan ID y código; componentes `ee` y `ec` separados |
| PDF páginas 10–11 + foto | 134 ubicaciones | La foto aporta IDs 51–107, no se concatena como un catálogo adicional |
| PDF página 12 | 37 modelos | Transcripción visual; nomenclatura pendiente de cotejar con placa |
| PDF páginas 1–2 | 90 trabajos + una fila de total | Histórico separado; la fila 91 no se contabiliza como trabajo |
| PDF página 3 | 4 solicitudes | Transcritas como revisiones, conservando estatus y fecha contradictorios |
| PDF página 13 | Resumen de frecuencias | Evidencia original, no servicios adicionales |

## Reglas de importación

- La importación es transaccional e idempotente: claves de ubicación/modelo, ID original de equipo y de trabajo. Una segunda ejecución no duplica ni sobrescribe ediciones operativas.
- `0000-00-00` pasa a fecha desconocida (`NULL`). `nd`/`0` de proveedor no generan proveedores ficticios. Costos de adquisición `0` se mantienen documentados en la fuente y como no informados en la ficha operativa. No se asume que todos los activos fueron gratuitos.
- El costo del histórico se conserva literalmente, sin asumir moneda ni que los ceros signifiquen gratuidad. Suma literal de trabajos: 150; concuerda con la fila de total 91. No se mezcla con costos en MXN capturados en nuevas órdenes.
- El estado inicial de los 318 componentes es **Por verificar**. No hay evidencia para declararlos todos operativos ni para inventar fechas futuras de mantenimiento.
- Se conservan 159 pares de códigos `ee`/`ec`. El prefijo sugiere evaporadora/condensadora; no se suman capacidades para anunciar capacidad instalada total ni se convierten automáticamente en 318 sistemas completos.
- `ee452` y `ec452` tienen ubicación literal `201`. No existe esa clave en el catálogo: quedan sin ubicación y con revisión pendiente. No se asume `f201`.
- Ocho componentes tienen modelo `nd`: pares 209, 278, 404 y 408. Se conservan sin modelo y con revisión.
- Los valores BTU atípicos (por ejemplo `pr04=6000`, `co01=48585`, `ma03=17697`) se conservan. La columna `piso_techo` de modelos está recortada; no se inventa su contenido.
- Hay 11 posibles repeticiones del histórico por equipo, concepto, fecha y costo. Se conservan sus IDs y se señalan como candidatas, sin eliminarlas automáticamente. La fila 26 parece tachada en el original y necesita interpretación humana.
- Algunas descripciones originales están truncadas o tienen errores: se conserva la referencia de página para cotejo. La fotografía y las páginas solo se sirven a usuarios autenticados.

La revisión no es certificación del estado físico. Marcar una excepción como verificada exige anotar la evidencia. La revisión por sí misma no cambia el equipo: primero editar el registro operativo correspondiente. Los históricos importados permanecen inmutables como evidencia; una corrección se documenta en la revisión y los nuevos trabajos en Órdenes.
