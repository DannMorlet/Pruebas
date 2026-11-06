# Morlet7 — Enrutado LM Studio y aislamiento de Promisory v0.4

Fecha 2026-10-29. **Estado:** código de preparación y pruebas simuladas. NO es prueba de juego jugable ni de NPU/GPU simultáneas.

## Por qué no podemos llamar Python desde .per o .ai

El juego carga `Nombre.ai` (marcador del jugador) y `Nombre.per` (reglas nativas). Los scripts .per NO arrancan Python ni envían HTTP a LM Studio. Es obligatorio iniciar el proceso Python aparte. Para observar una partida y enviar órdenes reales puede utilizarse, en una partida individual sin cheats, el **Agent Bridge v3** de AoE2Control. El puente también puede intercambiar goals con la IA nativa, pero esos IDs deben reservarse y validarse contra todos los includes antes de añadir un protocolo .per↔Python.

Fuentes: https://aoe2control.github.io/agent-bridge/ y https://aoeaidatabase.pythonanywhere.com/how_to

## Distribución exacta

| N.º | IA | Par del juego | Cliente externo Python | Carpeta aislada de soporte |
|---:|---|---|---|---|
| 1 | Matick | `Matick.ai` + `Matick.per` | `Matick.py` | `Morlet7_Matick_Core/` |
| 2 | Nemesis | `Nemesis.ai` + `Nemesis.per` | `Nemesis.py` | `Morlet7_Nemesis_Core/` |
| 3 | Tyran | `Tyran.ai` + `Tyran.per` | `Tyran.py` | `Morlet7_Tyran_Core/` |
| 4 | Mazapan | `Mazapan.ai` + `Mazapan.per` | `Mazapan.py` | `Morlet7_Mazapan_Core/` |
| 5 | Nutella | `Nutella.ai` + `Nutella.per` | `Nutella.py` | `Morlet7_Nutella_Core/` |
| 6 | Gemini | `Gemini.ai` + `Gemini.per` | `Gemini.py` | `Morlet7_Gemini_Core/` |
| 7 | Copilot | `Copilot.ai` + `Copilot.per` | `Copilot.py` | `Morlet7_Copilot_Core/` |

Además de los 7 clientes, **un solo** `morlet_router.py` administra las siete identidades y sus peticiones al modelo ya cargado en LM Studio. Los clientes individuales son puntos de entrada que usan `morlet_runtime.py`. En el ZIP entregado al usuario también se incluye `matick_bridge_base.py` con adaptación y validadores de Agent Bridge.

## Aislamiento real del motor HD original

Las siete versiones `.per` incluidas en el paquete v0.4 ya llaman `Morlet7_NOMBRE_Core\defaultConstants`, `Morlet7_NOMBRE_Core\finalingConstants` y `Morlet7_NOMBRE_Core\finaling`. **No tocan ni sobrescriben** `Promisory/`.

Para funcionar hay que copiar TODO el árbol original `Promisory/` desde la instalación propia y reescribir rutas internas en cada una de las siete copias aisladas. El preparador `IA/preparar_nucleos.py` del ZIP realiza esa operación en una carpeta temporal con política de no sobrescritura.

**Advertencia:** estas carpetas NO están incluidas en el ZIP: no se proporcionaron los módulos `defaultConstants.per`, `finalingConstants.per` y `finaling.per`. No instalar las nuevas referencias hasta prepararlas con una carpeta original compatible. No sustituirlas por los archivos AiBuilder subidos, pues no son necesariamente equivalentes.

## Enrutamiento de modelos

- **Granite 3.1 3B-A800M**: enrutador LM Studio preferido, API `http://127.0.0.1:1234/v1`.
- **Matick (#1)**: en v0.4 consulta el router; Gemma 4 de Matick queda como servicio especializado opcional futuro. No se inicia sola.
- **Nemesis (#2)**: Qwen3-0.6B en `C:\NPU`, inferencia OpenVINO real PENDIENTE de verificar. El router v0.4 no ejecuta dicho modelo.
- **Tyran y Mazapan (#3 y #4)**: comparten, cuando se integre, UN SmolLM2-360M en GPU; v0.4 usa el router para decisiones y no enciende otro modelo.
- **Nutella, Gemini, Copilot (#5–#7)**: sus políticas .per mantienen el juego; consultas especiales opcionales al router, sin un modelo individual adicional.

Esto evita duplicar pesos y garantiza que, si el enrutador se apaga, las reglas `.per` sigan intentando jugar.

## Uso en el ZIP v0.4 (no instalable hasta preparar núcleos)

```powershell
py IA\preparar_nucleos.py --fuente "C:\RUTA_REAL\ai\Promisory" --destino "IA"
py IA\morlet_router.py --jugadores Matick=2,Gemini=3 --simular
py IA\Matick.py --jugador 2 --simular
# Con el juego, Agent Bridge v3 y LM Studio activados (PREVIEW, no ejecuta):
py IA\morlet_router.py --jugadores Matick=2,Gemini=3 --modelo ID_EXACTO
# SOLO tras revisar resultados, autorizar órdenes reales:
py IA\morlet_router.py --jugadores Matick=2,Gemini=3 --modelo ID_EXACTO --execute
```

Los números en `--jugadores` son los slots reales del lobby, **no** los números 1–7 de la colección. Con `--execute`, una acción aceptada por el puente no significa necesariamente que ya se completó. Comprobar el resultado. Solo single-player, sin omnisciencia, desactivar Suppress Native AI, no desactivar Defender.

## Comprobaciones realizadas fuera de Windows

- 7 pares `.ai/.per` y 7 wrappers `.py`, más el router común y preparador.
- Compilación estática de los once `.py` del paquete.
- Simulación de `morlet_router.py` y cliente `Tyran.py` sin conexión real.
- Prueba de copiar módulos Promisory **de prueba** a siete carpetas distintas sin modificar el original y rechazando sobrescritura.
- Mock del bridge: PREVIEW no emite act; modo `--execute` sí lo solicitaría, con validación.

**Pendiente:** probar el origen verdadero `Promisory`, siete IA en el motor AoE2 DE, acciones de Agent Bridge reales, LM Studio real, las inferencias especializadas Intel NPU y SmolLM2, chats y estrategias complejas.

**No subir los siete .per completos a este repositorio público** hasta revisar los permisos de redistribución de la base de terceros. El ZIP entregado al usuario contiene la etapa v0.4 de preparación local.