# Gaming — integración prevista con LM Studio mcp.json

**Estado actual: plantilla y especificación, no instalación funcional.** El servidor indicado en la plantilla (C:\\Gaming\\mcp\\server.py) aún NO existe en la PC ni ha sido probado. No pegar esta configuración todavía en el mcp.json activo.

## Separar dos componentes

1. **Ventana Gaming:** proceso independiente con su propio interruptor ON/OFF, interfaz Matick / Local / Morlet y acoplamiento visual a la ventana de LM Studio. Un MCP **no inserta** widgets en el Model Server.
2. **Servidor MCP Gaming:** herramientas para consultar/controlar Gaming de manera autorizada desde LM Studio. Se registrará en mcp.json cuando el código esté probado.

## Plantilla para Codex

Consultar [ejemplo JSON](../examples/gaming.mcp.example.json). Este archivo es un **fragmento**, no el mcp.json completo. La única entrada nueva propuesta es la clave gaming dentro de mcpServers.

**No sobrescribir las claves existentes**: cursor, matick-echo, velocidad, refuerzo, agente-enrutador, mascota.mcp, chat_server.mcp, gemco-control, gemco-joystick. Pueden mantenerse los nombres antiguos de entradas técnicas; renombrarlos es una migración distinta y requiere respaldo y pruebas.

## Proceso de instalación futura

1. Identificar mcp.json **real** desde el botón mcp.json de LM Studio y respaldarlo con sello de fecha.
2. Verificar ruta real de Python y servidor, y que el proceso pase tests MCP (initialize, list tools, call tools y shutdown).
3. Fusionar la entrada gaming dentro del objeto mcpServers sin eliminar nada, usando parser JSON; validar claves, rutas y duplicados.
4. Registrar herramientas de bajo riesgo primero: gaming_status, gaming_open, gaming_close y gaming_list_chats (solo cuando estén implementadas).
5. Verificar que la interfaz no inicie inferencias, capturas, procesos auxiliares o herramientas al abrir LM Studio. Si el host MCP arranca el servidor al resolver herramientas, éste debe permanecer pasivo, sin trabajo recurrente.
6. Controlar acciones destructivas: borrar chat único/lotes/todo requiere autorización y confirmación en la UI; permisos granulares para control de PC.
7. Medir RAM/CPU y testear encendido/apagado repetido, desconexión y cierre. Mantener rollback inmediato para el mcp.json anterior.

## Limitación de activación

Registrar un comando en mcp.json **no garantiza** que LM Studio jamás inicie el proceso: el momento de lanzamiento depende del host y su configuración. Por ello el diseño requiere dos barreras:
- **Switch de Gaming en OFF**: proceso servidor en modo pasivo sin tareas costosas; si ya está ejecutándose, responde error de «Gaming desactivado» a herramientas de acción.
- **Habilitación de herramientas en LM Studio**: activar/invocar explícitamente el MCP solo cuando se necesite. Para OFF estricto de cero procesos, no registrar/habilitar el MCP en el host hasta que se use, o usar un mecanismo de habilitación oficial comprobado.

No inventar una propiedad "disabled": true sin confirmar que esa versión de LM Studio la admite.

## Uso desde LM Studio REST API v1

LM Studio 0.4+ puede referenciar un servidor ya declarado en mcp.json con una integración tipo "plugin" mediante ID mcp/gaming. La configuración de servidor indica que permitir acceso a MCP preconfigurados por API requiere activar "Allow calling servers from mcp.json" **y autenticación de API**. Habilitarlo solo para clientes de confianza. Para operaciones de PC, limitar allowed_tools y permisos del token.

Fuentes oficiales:
- https://lmstudio.ai/docs/app/mcp
- https://lmstudio.ai/docs/developer/core/mcp
- https://lmstudio.ai/docs/developer/core/server/settings

## Nombres visibles

Gaming (aplicación), Matick (asistente), Local (modelo y herramientas), Morlet (entorno central). No usar GemCo como marca de interfaz. Los IDs MCP preexistentes se preservan.
