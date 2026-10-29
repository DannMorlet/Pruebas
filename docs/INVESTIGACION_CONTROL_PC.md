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


## Recomendación personalizada — RTX 5060 8 GB, Core Ultra 5 225F, 32 GB DDR5-6000

**Decisión principal:** Matick en LM Studio con **Qwen3.5-4B Q4** como agente general; **MCP for Blender** (`ahujasid/mcp-for-blender`, nombre actualizado, paquete `mcp-for-blender`) para modificar escenas mediante `bpy` y código Python; **Windows-MCP** solo como capa de control de ventanas, teclado, mouse y elementos UIA; **AutoHotkey v2** opcional para macros repetitivas de muy baja latencia. Mantener los MCP preexistentes, inspeccionar primero y evitar funciones duplicadas.

### Modos de recursos

- **Gaming competitivo:** juego con prioridad sobre toda la VRAM; Gaming-Matick OFF de forma predeterminada. Si se necesitan tareas de IA puntuales, probar E2B o Qwen3.5-2B Q4 bajo demanda y descargar el modelo al terminar. No prometer ausencia de penalización de FPS.
- **Blender + Matick:** Qwen3.5-4B Q4, contexto inicial 4K–8K y herramientas de escena por `bpy`; limitar viewport/materiales según VRAM y evitar render Cycles GPU simultáneo con inferencia. Usar Windows-MCP para la UI solo si no hay API adecuada.
- **Calidad máxima (sin juego):** probar Qwen3.5-9B Q4; el modelo y caché pueden llenar casi toda la VRAM, así que reducir contexto o cambiar a Qwen3.5-4B cuando haya falta de memoria.

**Memoria:** tener 32 GB instalados NO permite mantener los 32 GB físicamente libres con Windows y Blender abiertos. Meta realista: evitar RAM offload del modelo, usar VRAM con margen, medir consumo de Windows y aplicaciones y poner límite al uso adicional de Gaming; descargar los modelos al dejar de usarlos.

### Por qué Blender-MCP en lugar de solo controlar el mouse

La API Python de Blender (`bpy`) permite operaciones deterministas y compuestas (crear mallas, asignar materiales, mover objetos, configurar luces, cámaras, guardar escenas), que ahorran ciclos captura→razonamiento→clic. El MCP de Blender expone información de la escena y ejecución de Python. Para drag-and-drop, cuadros de diálogo o acciones fuera de Blender, usar Windows-MCP con la intervención humana y control permitido.

**Cuidado:** la función de ejecutar código de Blender puede ejecutar Python arbitrario; usar `BLENDER_MCP_SAFE_MODE=1`, acceso del socket únicamente localhost y hacer copias de seguridad de .blend antes de ejecutar tareas. Esta protección es una barrera preventiva, no una garantía contra todo posible script.

### Integración gradual en mcp.json

- No pegar una plantilla que reemplace el archivo actual. Primero hacer backup, validar JSON, comparar IDs existentes y añadir exclusivamente la entrada `blender` a `mcpServers` si no existe.
- **Ejemplo de una sola entrada** (NO es un mcp.json completo; NO se instala hasta comprobar ruta real de uvx y addon):

```json
"blender": {
  "command": "uvx",
  "args": ["--python", "3.11", "mcp-for-blender"],
  "env": {
    "UV_PYTHON_PREFERENCE": "only-managed",
    "BLENDER_MCP_SAFE_MODE": "1",
    "DISABLE_TELEMETRY": "true"
  }
}
```

- La versión de Windows-MCP actual requiere Python >=3.14; usar un entorno virtual separado. El paquete MCP for Blender se puede ejecutar con `uvx` usando Python 3.11 gestionado por uv para esquivar incompatibilidades con Python 3.15.
- La opción `uvx mcp-for-blender setup` puede cambiar archivos de configuración; hacer `--dry-run` o una instalación manual controlada tras respaldos. Confirmar el procedimiento en la versión instalada.
- Apagado real: algunos clientes inician servidores MCP automáticamente al habilitarlos; un switch dentro de Gaming no garantiza cero procesos si el host los deja activos. Por eso, iniciar cuando se solicite, dejar servidores pasivos en reposo y verificar con el administrador de tareas.

### Datos verificados y pruebas pendientes

- Intel [Core Ultra 5 225F](https://www.intel.com/content/www/us/en/products/sku/241069/intel-core-ultra-5-processor-225f-20m-cache-up-to-4-90-ghz/specifications.html): 10 núcleos (6P+4E), NPU Intel AI Boost de 13 TOPS INT8; no dar por hecho que LM Studio pueda ejecutar sin ajustes modelos 2–9B en NPU.
- Google [Gemma 4](https://ai.google.dev/gemma/docs/core): E2B Q4_0 ~2.9 GB y E4B Q4_0 ~4.5 GB estimados con overhead; para Qwen3.5 Q4 2B/4B/9B usar medición de tamaño de modelo y KV cache en LM Studio, no interpretar el tamaño descargado como uso total.
- [Qwen3.5-4B en LM Studio](https://www.lmstudio.ai/models/qwen/qwen3.5-4b): ofrece visión y razonamiento; comprobar fiabilidad de llamadas a herramientas antes de dar por completada automatización de Blender.
- [MCP for Blender actualizado](https://github.com/ahujasid/mcp-for-blender), [Windows-MCP](https://github.com/CursorTouch/Windows-MCP) y [Blender hardware](https://www.blender.org/download/requirements/).

**Verificación requerida en PC:** medir 10 min CPU/RAM idle, picos VRAM y FPS de juego con modelo OFF y ON, ejecución segura de escena .blend de prueba, cancelación, restauración del usuario sobre el mouse y rollback del `mcp.json`.


## Actualización 2026-10-29 — Priorizar los modelos YA instalados

Se corrigió la estrategia anterior: **no descargar Qwen3.5-4B o 9B como requisito**, pues el usuario ya probó satisfactoriamente modelos propios en RTX 5060 8 GB. Los rótulos se tomaron de una captura de LM Studio; algunos nombres están truncados y Codex debe obtener IDs completos por API.

| Modelo existente | Rol inicial propuesto | Notas |
| --- | --- | --- |
| Matick Gemma 4 v2 E2B Q4_K_M | Asistente principal; evaluar herramientas/visión según capacidades reales | Está personalizado; no asumir que su GGUF se ejecuta directamente en Intel NPU |
| OLMoE 1B-7B-0125 Instruct Q4_K_S | Alternativa MoE para consultas simples; prueba de precisión y latencia | ~7B parámetros totales aunque ~1B activos por token; pesos totales ocupan VRAM |
| Qwen3.8 4B Agentic… Q4_K_S (etiqueta truncada) | Candidato a tareas agentic y código, condicionado a pruebas MCP | Resolver identificador exacto; no extrapolar soporte OpenVINO de otros Qwen |
| Granite 3.1 3B A800M Instruct Q4_K_S | Comandos breves y acciones estructuradas | ~3B totales, ~800M activos; probar formato de herramientas antes de automatización real |

### Decisión sobre NPU
- Intel Core Ultra 5 225F: Intel AI Boost NPU **13 TOPS INT8** según ficha Intel. La plataforma Arrow Lake NPU 3720 (PCI 0xAD1D) figura soportada en OpenVINO para Windows 11.
- **NPU experimental, jamás obligatoria:** la RTX 5060 sigue como inferencia principal, especialmente si el usuario ya tiene benchmarks positivos. La NPU 13 TOPS no debe asumirse más rápida ni con menor RAM efectiva para un LLM completo.
- **Primer candidato NPU: Gemma 4 E2B de referencia**, no necesariamente el GGUF personalizado: OpenVINO 2026.2 marca gemma-4-e2b-it FP4-NORMALIZED e INT8-CW como verificados en NPU, y las notas 2026.4 reportan mejoras de latencia inicial. Requiere un modelo en formato/precisión compatible, no abrir simplemente el Q4_K_M de LM Studio.
- **Mejor uso práctico para NPU si los LLM no rinden:** clasificación pequeña, embeddings/búsqueda y voz local *solo si existen modelos y pipelines verificados*; no activar cargas permanentes por defecto.
- Los cuatro modelos GGUF existentes permanecen en **LM Studio + RTX** mientras no haya pruebas controladas en el equipo. **El motor NPU debe ser un proceso separado, activado bajo demanda y con switch OFF**.
- OpenVINO incluye soporte de SDK Python para versiones específicas; usar entorno virtual compatible, no sustituir C:\Python315\python.exe. Verificar driver NPU/versión, `from openvino import Core; print(Core().available_devices)` antes de conversiones o descargas.
- OLMoE y Granite indicados no se declaran NPU-compatibles sin test o soporte publicado. No asumir que la compatibilidad de una familia se extiende a una variante personalizada/finetune.

### Prueba A/B propuesta para Codex local
1. Medir en LM Studio con cada uno de los cuatro modelos: tokens/seg, TTFT, tool-call correcto, VRAM, RAM, CPU, FPS de juego cuando corresponda. Mismo prompt de 10 acciones y contexto equivalente.
2. Verificar en Windows Device Manager el driver NPU y en OpenVINO que exista `NPU` en `Core().available_devices`. No instalar drivers a ciegas.
3. Solo si está disponible, ejecutar inferencia de prueba con un **modelo OpenVINO compatible** en NPU y comparar **sin cambiar** el GGUF existente. Medir memoria total y CPU también.
4. Adoptar NPU únicamente si reduce carga de GPU en una tarea útil sin ralentizar Matick ni perjudicar FPS; en otro caso dejarla apagada.

Fuentes: https://www.intel.com/content/www/us/en/products/sku/241069/intel-core-ultra-5-processor-225f-20m-cache-up-to-4-90-ghz/specifications.html ; https://github.com/openvinotoolkit/openvino/blob/master/src/plugins/intel_npu/README.md ; https://docs.openvino.ai/2026/documentation/compatibility-and-support/supported-models.html ; https://docs.openvino.ai/2026/about-openvino/release-notes-openvino.html ; https://huggingface.co/allenai/OLMoE-1B-7B-0125-Instruct-GGUF ; https://huggingface.co/tensorblock/granite-3.1-3b-a800m-instruct-GGUF .
