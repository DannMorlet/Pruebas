# Gaming · Arquitectura prevista

**No implementada todavía.** El objetivo es una aplicación compañera de LM Studio Model Server que parezca integrada sin modificar su ejecutable.

## Componentes propuestos
1. UI nativa Windows: PySide6/Qt o WinUI 3.
2. Controlador de acoplamiento: escuchar eventos de ventanas Win32 y aplicar geometría con DPI correcto; no hacer polling intensivo.
3. Cliente HTTP local: consultar modelos y enviar chats bajo demanda al servidor OpenAI-compatible de LM Studio en localhost:1234.
4. Administrador de servicio: OFF inicial, ON explícito, parada y recuperación sin procesos duplicados.
5. Historial SQLite local con consultas paginadas y transacciones para borrado por lotes.
6. Adaptadores MCP, habilitados por separado con permisos explícitos y logs mínimos.

## Compatibilidad
Máquina de referencia declarada: Windows 11, Python 3.15, RTX 5060 8 GB, RAM 32 GB, LM Studio 0.4.26. La API, IDs y compatibilidad real deben verificarse en ejecución.

**No sobrescribir** MCP existentes: cursor, matick-echo, velocidad, refuerzo, agente-enrutador, mascota.mcp, chat_server.mcp, gemco-control y gemco-joystick. Los dos últimos conservan nombres internos históricos aunque la marca UI sea Gaming.

Evitar publicar credenciales, tokens, datos privados o rutas sensibles en repositorio público. Conexiones fuera de localhost requieren puente autenticado, HTTPS y autorización.

## Seguridad y errores
Permiso por tipo de acción para pantalla, mouse, teclado y archivos. Detención de streaming, tiempos máximos de espera, cancelación y rollback de cambios. No ejecutar nada por defecto.
