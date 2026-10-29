# Instrucciones para Codex — Gaming / Matick

## Identidad del producto
- **Gaming**: nombre de la aplicación (no usar GEMCO como marca).
- **Matick**: asistente/experiencia conversacional.
- **Local**: motor de LM Studio, estado de modelo y MCP.
- **Morlet**: espacio central de proyectos, tareas y chats.
- La estética de referencia es Codex/ChatGPT Work, con diseño original. No denominar las secciones Sol, Luna o Terra.

## Objetivo inmediato
Implementar una aplicación **Windows nativa y ligera** tomando como referencia el prototipo `prototype/index.html` (visual solamente), y no limitarse a escribir más documentos. Empieza por un MVP ejecutable en modo demostración, con paneles redimensionables/plegables, modo compacto vertical, switch OFF, chats de ejemplo y pruebas.

## Componentes e integración
- La app debe funcionar como ventana compañera a `LM Studio > Model Server` con acoplamiento visual adaptable; **no** inyectar en LM Studio ni modificar su ejecutable.
- Conector local LM Studio OpenAI-compatible a `127.0.0.1:1234` solo bajo solicitud. Detectar modelo cargado en runtime, no asumir que está cargado ni auto-cargarlo.
- El MCP Gaming será **un segundo componente**, y solo cuando su servidor esté desarrollado y probado se fusionará su entrada en el `mcp.json` real, previa copia de seguridad. No sustituir todo el JSON.
- Conservar sin renombrar los identificadores MCP actuales: `cursor`, `matick-echo`, `velocidad`, `refuerzo`, `agente-enrutador`, `mascota.mcp`, `chat_server.mcp`, `gemco-control`, `gemco-joystick`.
- No escribir ni modificar rutas locales reales del usuario desde Codex Cloud; solo scripts reproducibles y un procedimiento seguro de instalación.

## Ciclo de vida seguro
- Gaming OFF por defecto y tras reiniciar: no realizar inferencia, captura de pantalla, polling, tareas recurrentes ni iniciar procesos auxiliares.
- Si LM Studio inicia servidores MCP al cargar la configuración, un MCP habilitado puede existir como proceso pasivo: no prometer cero procesos con solo un switch de UI. Documentar/hacer que la habilitación MCP en LM Studio sea explícita cuando se necesite.
- Solo una instancia, cancelación de streaming, desconexión y cierre limpio.
- Control de PC (mouse, teclado, ventanas, visión dual monitor) solo con permisos explícitos y límites.

## Rendimiento y UX
- Priorizar PySide6/Qt o WinUI 3 (investigar compatibilidad Python 3.15 antes de elegir).
- No usar Chromium/Electron extra por defecto.
- Sidebar izquierda y panel derecho: acoplados/desacoplados, colapsables, anchos ajustables sin bloquear el chat.
- Debe estirarse tanto horizontal como verticalmente, seguir LM Studio al moverlo, cambiar DPI, minimizar/maximizar, y pasar entre los dos monitores verticales (principal izquierdo 300 Hz; secundario derecho 75 Hz). Verificar índices reales, DPI y coordenadas; no inventarlos.
- SQLite local con paginación. Vaciar conversación, borrar individual, seleccionar en lote, borrar todo con confirmación. No tocar chats externos.
- Registrar CPU/RAM, detectar fugas y probar ajustes de ventana y apagado; el crecimiento previo comunicado de RAM era cercano a 1 GB y no se debe declarar solucionado sin medición.

## Archivos para empezar
- `README.md`
- `prototype/index.html`
- `docs/UX.md`
- `docs/ARQUITECTURA.md`
- `docs/CODEX_HANDOFF.md`
- `docs/MCP_JSON.md`
- `examples/gaming.mcp.example.json`

## Entregables esperados
1. Código funcional y pruebas mínimas automatizadas (en una rama/PR).
2. Script local de instalación/ejecución con venv sin instalar drivers ni exigir servicios pagados.
3. Prueba de modo demo y política de inicio OFF.
4. Cliente de LM Studio con errores claros.
5. Integración MCP implementada y validada *antes* de proponer cambios al `mcp.json` del usuario.
6. Reporte honesto de lo que solo puede verificarse desde Windows con LM Studio instalado; nunca afirmar pruebas locales realizadas en Codex Cloud.

> Importante: el repositorio es público. No subir claves, tokens, datos privados, contraseñas, chats reales, capturas personales ni IP de la LAN.
