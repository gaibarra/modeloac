# Modelo AC · Escuela Modelo

Aplicación institucional para el inventario y cuidado de los equipos de aire acondicionado. Next.js + TypeScript, Django REST Framework, Gunicorn, PostgreSQL; plantillas exclusivas de Nginx/systemd y HTTPS pendiente del dominio.

## Incluye

- Acceso por sesión, CSRF, roles y cambio de contraseña.
- Tablero con cifras reales, distribución por edificio y alertas de calidad.
- Inventario editable, garantías, modelos técnicos, ubicaciones y proveedores.
- Adquisiciones con estado, factura, cantidad y presupuesto.
- Órdenes preventivas/correctivas, checklist, agenda y cálculo de próxima fecha.
- Histórico original separado y auditoría de cambios operativos.
- Siete reportes exportables a CSV, Excel y PDF; simulador de energía.
- Revisión de fuentes con imágenes autenticadas, referencias e importación idempotente.

## Datos importados

**318 componentes**, **134 ubicaciones**, **37 modelos** y **90 intervenciones históricas**. La fila 91 del reporte es un total, no un trabajo. La foto complementa los IDs de ubicación 51–107 y no genera duplicados. Se detectaron **11 posibles repeticiones históricas**, dos componentes con ubicación `201` no conciliada y ocho sin modelo. Ningún activo se declara operativo por suposición.

Las cantidades no equivalen a 318 sistemas completos: el original separa evaporadoras y condensadoras. Consulta [conciliación de origen](docs/DATOS-ORIGEN.md).

## Vista previa local

En el servidor: `http://127.0.0.1:3108`. Desde otro equipo, abrir un túnel SSH según [despliegue](docs/DESPLIEGUE.md). Credenciales iniciales en `.work/acceso-inicial.json` (archivo privado, ignorado por Git). No se ha publicado un dominio ni emitido certificado.

## Desarrollo

Requiere Node.js 20.9+ (se probó 20.20.2), Python 3.10+ y Docker Compose para PostgreSQL aislado.

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
npm ci --prefix frontend
cp .env.example .env
# Editar .env: generar claves reales y definir POSTGRES_PASSWORD.
chmod 600 .env

docker compose --env-file .env -f compose.db.yml up -d
set -a
source .env
set +a
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py setup_roles
.venv/bin/python backend/manage.py import_inventory data/initial_inventory.json --dry-run
.venv/bin/python backend/manage.py import_inventory data/initial_inventory.json
.venv/bin/python backend/manage.py createsuperuser
.venv/bin/python backend/manage.py collectstatic --noinput
# Terminal 1:
scripts/run-backend.sh
# Terminal 2 (alternativa desarrollo):
npm run dev --prefix frontend
```

Los scripts locales contienen la ruta `/home/gaibarra/modeloac`; ajustarla si se cambia de servidor. Producción utiliza las imágenes y la unidad propias en `infra/`. No reemplazar configuraciones de aplicaciones existentes.

## Validación

```bash
set -a
source .env
set +a
.venv/bin/python backend/manage.py check
.venv/bin/python backend/manage.py test inventory --noinput
npm run build --prefix frontend
cd frontend
PLAYWRIGHT_SKIP_BROWSER_GC=1 npx playwright test
```

Las pruebas backend crean y destruyen su propia base `test_modeloac`; no ejecutarlas con una URL de base ajena. Las pruebas de navegador usan la vista previa y el acceso inicial privado; si se cambió la clave, actualizar la credencial local de pruebas o configurar una cuenta dedicada. No se realizan altas operativas desde la prueba de recorrido.

## Documentación

- [Guía de operación](docs/GUIA-USO.md)
- [Conciliación del PDF y fotografía](docs/DATOS-ORIGEN.md)
- [Despliegue aislado y HTTPS](docs/DESPLIEGUE.md)
- [Referencia visual original](docs/REFERENCIA-VISUAL.md)
- [Captura del tablero](docs/screenshots/dashboard-desktop.png)

Los archivos originales permanecen intactos. No se incluyen datos ficticios de proveedores, compras, garantías o estados de funcionamiento.
