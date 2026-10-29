# Investigación para Gaming / Matick — control de Windows rápido y ligero

Fecha de consulta: 2026-10-29. **Referencias verificadas**, no instalaciones ni benchmarks realizados en la PC del usuario.

## Conclusión

Para control de escritorio por IA, **evaluar Windows-MCP antes de construir nuevas herramientas**. Para el motor que exige latencia y sobrecarga mínimas, priorizar API nativas **Windows UI Automation + Win32 SendInput** y acciones de alto nivel. Capturar pantalla solo cuando se necesite. Para controlar la PC desde Android jugando, usar **Sunshine + Moonlight** bajo demanda: no exigir a un LLM que mueva cada píxel del mouse. No instalar nuevos drivers de gamepad si no se comprueba primero ViGEmBus/estado actual.

## Recursos por objetivo

| Recurso | Para qué sirve | Nota de rendimiento |
|---|---|---|
| [Windows-MCP de CursorTouch](https://github.com/CursorTouch/Windows-MCP) | MCP listo para PC Windows: inventario de displays/DPI, Screenshot, Snapshot UIA, Click, Type, Move, App, Process, FileSystem y más | Es liviano en intención pero incluye varias dependencias; benchmarking local imprescindible |
| [pywinauto](https://github.com/pywinauto/pywinauto) | Acciones directas sobre controles Win32/UI Automation desde Python | Evita capturas para controles accesibles |
| [AutoHotkey v2](https://github.com/AutoHotkey/AutoHotkey) | Atajos y macros deterministas, sin invocar LLM por acción | Candidato para mínima latencia de input |
| [Microsoft UFO²](https://github.com/microsoft/UFO) | Arquitectura de agentes con UIA/Win32/WinCOM y control híbrido | Investigación de diseño, no stack inicial de mínimo consumo |
| [DXcam](https://github.com/ra1nty/DXcam) | Captura Windows mediante Desktop Duplication / WinRT | Flujo rápido a petición; comprobar Python 3.15 |
| [MSS](https://github.com/BoboTiG/python-mss) | Capturas de uno o varios monitores sin dependencias externas | Plan B simple de captura |
| [Sunshine](https://github.com/LizardByte/Sunshine) + [Moonlight Android](https://github.com/moonlight-stream/moonlight-android) | Escritorio y juegos desde teléfono, vídeo con codificación NVIDIA NVENC | Prioridad si se busca baja latencia con control táctil/controles |
| [KDE Connect](https://apps.kde.org/kdeconnect/) | Control simple de mouse/teclado del PC desde Android | Alternativa sin streaming de vídeo de juegos |
| [RustDesk](https://github.com/rustdesk/rustdesk) | Escritorio remoto general/self-hosting | Alternativa para soporte remoto, no prioridad en gaming |

## Propuesta de arquitectura

```
Gaming (ventana ligera, switch OFF inicial)
  └─ Matick (modelo cargado LM Studio, solicitud explícita)
      └─ agente-enrutador EXISTENTE (examinar antes de duplicar)
          ├─ acciones UIA/Win32 (sin captura): ventanas, controles, teclado/mouse, archivos autorizados
          ├─ captura a petición: DXcam -> fallback MSS, con escala/recorte y 2 monitores
          ├─ MCP existente: cursor, chat_server.mcp, refuerzo, velocidad, etc.
          └─ Sunshine + Moonlight: streaming táctil de bajo retardo cuando el usuario lo active
```

Enviar primero acciones tipadas y lotes deterministas; no generar cientos de ciclos "screenshot → LLM → click". Mantener kill switch y autorización por herramienta. Priorizar siempre API de aplicación antes que la interfaz gráfica cuando proceda.

## Hallazgos técnicos importantes

1. **Windows-MCP (CursorTouch)** permite capturar `display=[0,1]`, recortar por `region`, consultar display inventory y aplicar políticas `relaxed`, `balanced` o `strict`; su documentación da una latencia típica de 0.2–0.5 s entre acciones (NO equivale a una respuesta de mouse a 300 Hz). Tiene política de control físico del usuario y takeover. Se pueden limitar herramientas por `WINDOWS_MCP_TOOLS`, excluir funciones peligrosas y reducir capturas usando `WINDOWS_MCP_SCREENSHOT_SCALE`. La telemetría anónima puede desactivarse con `ANONYMIZED_TELEMETRY=false`.
2. Windows-MCP dice requerir Python >=3.14, pero **DXcam publica wheels oficiales para CPython 3.10–3.14**, no 3.15 en la documentación consultada. No suponer que las dependencias nativas instalan correctamente en el Python `C:\Python315\python.exe`. Codex debe crear un entorno aislado con una versión soportada si hace falta; **no sustituir la instalación Python 3.15 del usuario**.
3. **MSS** es Python puro con ctypes y tiene soporte multi-monitor, útil como fallback o baseline para métricas.
4. **UFO²** combina UI Automation y comandos de apps; tomar de él estrategia de acciones híbridas y orquestación, sin asumir que su arquitectura cabe en el presupuesto de RAM de Gaming.
5. **Sunshine** admite NVENC en Windows; para gamepad virtual se deben examinar controladores compatibles, pero **ViGEmBus NO se reinstala** sin comprobar lo ya instalado y documentar permisos.
6. Documentación de Microsoft sobre [SendInput](https://learn.microsoft.com/windows/win32/api/winuser/nf-winuser-sendinput), [UI Automation](https://learn.microsoft.com/windows/win32/winauto/entry-uiauto-win32) y [EVENT_OBJECT_LOCATIONCHANGE](https://learn.microsoft.com/windows/win32/winauto/event-constants): para un panel acoplado a LM Studio, el último detecta cambios de tamaño/posición de la ventana superior; cambios internos de paneles pueden requerir inspección UIA o anclaje manual.
7. Seguridad: Windows-MCP ofrece capacidades amplias (PowerShell, registro, archivos, procesos). Para Gaming, **desactivarlas por defecto**; habilitar a petición tras aprobación. Mantener TCP/HTTP en localhost, y si hay remoto exigir autenticación/HTTPS o VPN privada. Ningún acceso a PC por solo insertar mcp.json.

## Pruebas para Codex en Windows

- Primero inventariar y respaldar MCP reales; comparar si `gemco-control`, `cursor` y `agente-enrutador` ya hacen lo mismo.
- Confirmar indicadores de display, resolución física y DPI del monitor principal izquierdo vertical (300 Hz) y secundario derecho vertical (75 Hz) mediante DisplayInventory; no asumir índices.
- Preparar entorno virtual con Python compatible, ejecutar Windows-MCP con permisos mínimos **solo en una sesión de pruebas**, sin incorporarlo todavía al mcp.json productivo.
- Probar operaciones: listar ventanas, enfocar Bloc de notas, escribir texto de ejemplo, capturar recorte de pantalla, cerrar el proceso de prueba.
- Medir CPU/RAM idle por 10 min, memoria máxima, tiempo de captura, latencia del input, efecto de resize y reconexión; comparar con scripts Win32/pywinauto y con el MCP existente.
- Ninguna captura continua ni streaming activo con Gaming OFF.
- Probar retorno a control manual y cierre de servicios sin procesos huérfanos; conservar mcp.json antiguo y un plan de rollback.

## Fuentes oficiales

- https://github.com/CursorTouch/Windows-MCP
- https://github.com/CursorTouch/Windows-MCP/blob/main/pyproject.toml
- https://github.com/ra1nty/DXcam/blob/main/pyproject.toml
- https://github.com/BoboTiG/python-mss
- https://github.com/pywinauto/pywinauto
- https://github.com/AutoHotkey/AutoHotkey
- https://github.com/microsoft/UFO
- https://github.com/LizardByte/Sunshine
- https://github.com/moonlight-stream/moonlight-android
- https://learn.microsoft.com/en-us/windows/win32/winauto/event-constants
- https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput

**Estado:** documento de investigación; no se ha instalado ni conectado nuevo software a la PC del usuario. Se debe implementar en rama y validar con Codex local.
