# Matick #1 — Age of Empires II DE + LM Studio (puente experimental v0.1)

**Hay exactamente siete IAs y Matick es la número 1.** Esta carpeta solo integra el cerebro externo de **Matick**; no reemplaza `Matick.per` ni altera las otras seis IAs. El `.per` se encarga de la economía y el combate mientras el LLM sugiere acciones especiales.

## Estado real

- Probado: sintaxis de Python, políticas en tests sin juego y modo `--simular`.
- **No probado**: Agent Bridge, LM Studio ni AoE2 DE ejecutándose en tu PC Windows 11.
- El motor externo de AoE2Control v1.1.1+ usa un **named pipe** (`\\.\pipe\AoE2ControlAgentV3.P<n>`) y el contrato JSON v3. No mueve el mouse ni el teclado.
- **Aviso de seguridad:** AoE2Control funciona mediante inyección de una DLL en el proceso del juego. Examina su código/procedencia, las condiciones del juego y las advertencias del antivirus antes de instalarlo. **No desactives Defender ni agregues excepciones automáticamente.** No está integrado ni distribuido en este ZIP.
- El software del puente no soporta órdenes en multijugador. Utilizar únicamente **partidas individuales sin cheats**. No activar `Modules See Everything`.

## Preparación

1. Haz backup de tus `.per`, `.ai`, `Promisory`, partidas y configuración de mods. No reemplazar archivos ajenos sin permiso.
2. Instala `Matick.ai` y `Matick.per` de la versión corregida junto a la **carpeta `Promisory` legítima completa** de la IA HD. No está incluida en el proyecto.
3. Verifica que LM Studio tenga **Model Server** encendido y tu modelo Matick cargado. API: `http://127.0.0.1:1234/v1`. No carga otro modelo automáticamente.
4. Si decides utilizar AoE2Control, consulta su documentación oficial: https://aoe2control.github.io/agent-bridge/ . Necesitas una edición compatible del juego y la versión **1.1.1+**. **No usar el viejo pipe V1**.
5. En **CONTROL > Modules**, activa `Agent Bridge` y **solo** el jugador correspondiente a Matick. Para conservar la IA `.per` NO actives `Suppress Native AI`. Desactiva `Modules See Everything`.
6. En partida, identifica el ID de jugador real (1–8). Frecuentemente Matick será jugador 2; no confundir con el número de IA en el proyecto.

## Pruebas por pasos (sin instalar dependencias Python)

Abre PowerShell en esta carpeta, usando Python 3.15 si está disponible:

```powershell
C:\Python315\python.exe matick_agent.py --simular
C:\Python315\python.exe matick_agent.py --modelos
C:\Python315\python.exe matick_agent.py --status --player 2
C:\Python315\python.exe matick_agent.py --once --player 2
```

El último comando pregunta una decisión a LM Studio pero **NO la envía al juego**. Primero revisa lo que imprimió.

Después de verificar todo y solamente en una partida individual:

```powershell
C:\Python315\python.exe matick_agent.py --once --player 2 --execute
```

La ejecución continua es **opt-in**, no inicia con Windows ni LM Studio:

```powershell
C:\Python315\python.exe matick_agent.py --loop --player 2 --interval 45 --execute
```

Pulsa **Ctrl+C** para finalizar. Si hay varios modelos cargados, usa `--model "ID-EXACTO"` tomado de `--modelos`.

## Seguridad y rendimiento

- Máximo 2 acciones por ciclo, 2 aldeanos entrenados por ciclo, un máximo de 8 unidades movidas por comando. No autoriza borrar unidades, rendirse, intervenir en otros procesos ni modificar recursos artificialmente.
- `player.tribute.v1` permite enviar recursos incluso a un enemigo **si el juego lo admite**, con mercado construido, tarifa de tributo y tope de 100 unidades por orden. No garantiza poder pagarlo. **Nunca genera recursos**.
- El agente rechaza modo omnisciente, usa la vista del jugador y no solicita capturas de pantalla.
- En un juego compartido, el `.per` y Matick externo pueden competir por controlar las mismas unidades: por eso empieza con `--once` y mide conflictos. Para control más avanzado, planear intercambio de `player.set_goals.v1` con IDs verificados sin colisionar con goals existentes.
- Los modelos pequeños pueden devolver respuestas JSON mal formadas o equivocarse con IDs: esas respuestas se **descartan**, no se ejecutan. El juego sigue validando cada comando.
- Si la respuesta del LLM tarda más que la duración de la sesión Agent Bridge, puede expirar. Se reporta el error; la versión v0.1 no promete recuperación automática sin riesgo.
- No carga 7 modelos ni 7 puentes a la vez. Los 32 GB físicos no estarán totalmente libres mientras Windows y el juego estén activos.

## Fuentes

- https://aoe2control.github.io/agent-bridge/
- https://github.com/aoe2control/AoE2Control
- https://lmstudio.ai/docs/developer/openai-compat
- https://lmstudio.ai/docs/developer/openai-compat/tools

### Comprobación de tests

```powershell
C:\Python315\python.exe -m unittest discover -s tests -v
```

**La integración de Nemesis/NPU, Tyran, Mazapan y demás IAs permanece separada.** No existe una conexión de LM Studio solo por nombrar al archivo `.per`; este programa externo es el intermediario.