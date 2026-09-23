# Legibilidad y comodidad visual

Actualización del 22 de septiembre de 2026 para Modelo AC.

- Tipografía del sistema: Segoe UI en Windows, con alternativas nativas en otros dispositivos.
- Texto principal y formularios a 16 px; tablas y acciones a 15 px; etiquetas secundarias a 13–14 px. Tamaños expresados en rem para respetar preferencias del navegador.
- Mayor contraste en textos secundarios, encabezados y estados. Los estados conservan texto además del color.
- Controles de al menos 44 px, entradas de 48–52 px y foco visible para navegación con teclado.
- Filas alternadas y resaltado al pasar el cursor, códigos subrayados y mejor separación de columnas.
- Menú desplegable en móvil y tableta; tablas con desplazamiento horizontal dentro de su contenedor. Formularios y reportes se reorganizan en una columna.
- Se conserva la paleta institucional y el comportamiento de la aplicación.

Implementación: frontend/src/app/globals.css. Publicación limitada al contenedor frontend de modeloac-prod, sin migraciones ni modificaciones a los datos.

Validación final: compilación Next.js y TypeScript correctas; pruebas de navegador en producción a 1366, 1024, 768 y 390 px, con inventario, apertura de formularios, reportes y cierre de sesión. Sin desbordamiento de página ni errores JavaScript. Frontend saludable y endpoint de salud correcto. Las 14 respuestas de otros sitios y sus configuraciones permanecen iguales.
