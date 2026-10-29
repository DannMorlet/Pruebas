# Gaming / Matick · Morlet Workspace

> **Estado:** prototipo visual y especificación de producto. **NO está integrado a LM Studio y NO modifica sus MCP ni su ejecutable.**
>
> Diseño de referencia: ChatGPT/Codex, adaptado a **LM Studio 0.4.26**, Windows 11 y los modelos locales del usuario.

## Identidad definitiva

**Marca visual elegida por el usuario: Gaming.** Los identificadores internos de MCP existentes no se renombran sin migración controlada.

- **Matick:** asistente y experiencia de chat con el modelo cargado en LM Studio.
- **Local:** conexión local a modelos, herramientas MCP y recursos de la PC.
- **Morlet:** espacio central para proyectos, chats, historial y flujos de trabajo.
- **Gaming:** nombre global del entorno. **No usar Sol, Luna ni Terra** como nombres del producto.

## Entregables

| Archivo | Propósito |
| --- | --- |
| Prototipo visual (pendiente) | Se diseñará y verificará antes de la implementación con Codex |
| [Especificación UX](docs/UX.md) | Paneles, modos, switch y administración de conversaciones |
| [Arquitectura](docs/ARQUITECTURA.md) | Integración segura con LM Studio / Windows / MCP, ciclo de vida, memoria |
| [Trabajo para Codex](docs/CODEX_HANDOFF.md) | Pasos y criterios de aceptación antes de implementar |

## Estado de los entregables

La documentación de diseño está disponible. **El prototipo navegable todavía no está publicado**; no hay aplicación instalada ni conexión con LM Studio en este repositorio.

## Experiencia deseada

1. Diseño **oscuro, compacto y tipo Codex**, con barra de herramientas y área central.
2. Panel izquierdo y panel derecho **independientes, acoplables/desacoplables y redimensionables**. El contenido ocupa inmediatamente el espacio libre.
3. Sigue a LM Studio al cambiar tamaño, minimizar o mover la ventana, incluso con DPI o monitores distintos, en la aplicación futura.
4. **Interruptor apagado por defecto**: sin iniciar servicios, MCP, inferencias, ventanas o capturas en segundo plano.
5. Chats propios: nuevo chat, fijar, seleccionar múltiples, eliminar por lotes, vaciar uno y borrar todo (con confirmación y sin afectar datos de LM Studio).
6. **Bajo consumo de RAM/CPU**: objetivos medibles, no afirmar rendimiento hasta tener pruebas.
7. Nunca sobrescribir `chat_server.mcp`, `cursor`, `matick-echo`, `velocidad`, `refuerzo`, `agente-enrutador`, `mascota.mcp`, `gemco-control` ni `gemco-joystick`.

## Ambiente de referencia

- Windows 11; Python `C:\Python315\python.exe`
- RTX 5060 de 8 GB; 32 GB RAM
- LM Studio 0.4.26 y modelo local `matick-gemma-4-e2b-mexicano-v2`
- Servidor local por defecto: `http://127.0.0.1:1234`
- No incluir claves, tokens, IP privadas, capturas personales o historiales reales en este repositorio **público**.

## Fuentes oficiales para implementación

- [LM Studio REST API v1](https://lmstudio.ai/docs/developer/rest)
- [LM Studio MCP vía API](https://lmstudio.ai/docs/developer/core/mcp)
- [Servidor local de LM Studio](https://lmstudio.ai/docs/developer/core/server)

### Principio de implementación

El objetivo es que **se vea integrado** a la vista Model Server, pero no se presupone una API oficial de LM Studio para inyectar paneles en su interfaz. El primer enfoque seguro a evaluar es una **ventana compañera nativa con acoplamiento visual mediante las API de ventanas de Windows**, sin DLL injection ni parches al ejecutable. La implementación real deberá validar los límites de este enfoque y obtener consentimiento para control de pantalla/PC.

## Integración obligatoria con mcp.json

**Antes de dar Gaming por implementado**, Codex debe registrar el servidor de herramientas en el `mcp.json` real de LM Studio, previa copia de seguridad, pruebas de arranque y fusión sin perder entradas existentes. Ver [guía MCP](docs/MCP_JSON.md) y [plantilla no activada](examples/gaming.mcp.example.json). La interfaz acoplable es un componente distinto: `mcp.json` no modifica la UI de LM Studio. La plantilla no debe instalarse hasta que exista y se pruebe `server.py`.
