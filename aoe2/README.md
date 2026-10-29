# Morlet AoE2 DE — siete IAs

Este subdirectorio contiene una **configuración y una prueba aislada** para el proyecto de siete IAs; no sustituye a los archivos .per ni instala modelos.

## Archivos

- agents.json: alineación numerada 1–7, motores, límites y recursos optativos.
- subagents_gpu.py: consulta experimental de LM Studio para Tyran/Mazapan; SIN control del juego, mouse ni teclado.
- ../docs/AOE2_7_IAS_ARQUITECTURA.md: arquitectura, riesgos, objetivos e integración futura.
- ../tests/test_aoe2_subagents.py: tests sin hardware.

## Probar sin conectar ningún modelo

Desde la raíz de Pruebas en PowerShell:

    C:\Python315\python.exe aoe2\subagents_gpu.py --agente Tyran
    C:\Python315\python.exe aoe2\subagents_gpu.py --agente Mazapan
    C:\Python315\python.exe -m unittest discover -s tests -p "test_aoe2_subagents.py"

La salida SIMULACIÓN es un ejemplo, no una decisión del LLM.

## Consulta real de un modelo previamente cargado en LM Studio

Solo después de cargar manualmente un modelo pequeño en LM Studio y copiar su ID exacto:

    C:\Python315\python.exe aoe2\subagents_gpu.py --agente Tyran --modelo ID_EXACTO --consultar --estado "{\"aldeanos\":6,\"enemigos_visibles\":2,\"food\":130}"
    C:\Python315\python.exe aoe2\subagents_gpu.py --agente Mazapan --modelo ID_EXACTO --consultar

Los dos comandos pueden apuntar al MISMO ID de modelo y usar distintos prompts. Solo solicitan texto a LM Studio; **NO envían comandos a Age of Empires**, no modifican .per, no cargan automáticamente un GGUF y no permiten comandos arbitrarios.

## Qué falta

- Conectar las propuestas validadas al puente Agent Bridge para que el juego reciba órdenes.
- Probar que las siete IAs trabajan aun con el puente apagado.
- Hacer pruebas de consumo real, FPS, fiabilidad del JSON y compatibilidad con la versión del juego.
- Incorporar el diseño de Gemini y Copilot cuando el usuario lo comparta, respetando lo que cada uno dijo.
- Comprobar versiones de Promisory que ya están instaladas; no sobrescribir sin backup.

## Siete archivos AI y siete PER: construcción reproducible v0.3

Los archivos generados se entregan al usuario como ZIP en la conversación de ChatGPT. El repositorio público **NO contiene copias de la IA HD de terceros**. Sí contiene el código para reconstruirlas a partir del ZIP de origen que el usuario ya posee.

Script: [build_7_ias.py](build_7_ias.py). Utiliza exclusivamente la biblioteca estándar de Python.

En PowerShell desde la raíz del repositorio:

```powershell
py aoe2\build_7_ias.py --base "C:\ruta\Morlet_AoE2DE_7IAs_Matick_LMStudio_v0_2.zip" --out "C:\IA\Morlet\siete_ias"
```

El resultado contiene exactamente: Matick.ai/.per, Nemesis.ai/.per, Tyran.ai/.per, Mazapan.ai/.per, Nutella.ai/.per, Gemini.ai/.per, Copilot.ai/.per, más AUDITORIA.json.

**Dependencia imprescindible:** carpeta Promisory legítima compatible con la versión del motor HD; en particular defaultConstants.per, finalingConstants.per y finaling.per. Sin ella no se declara jugable.

**Versión v0.3:** añade preferencias .per conservadoras de las siete personalidades, que NO reemplazan el puente a LM Studio/NPU ni simulan 500 frases en el chat. Gemini incorpora metas económicas del PDF por edad y Nutella una expansión secundaria. Zero cc-add-resource en las versiones generadas. Comprobar en partida real antes de declarar que cada IA funciona.

**No subir el ZIP de las versiones HD derivadas a este repositorio público** hasta verificar derechos y licencias aplicables. Las personalidades, roles, especificaciones y generador son archivos originales del proyecto.

## Versión v0.4 — Python externo y `Promisory` aislado

**Aviso:** el paquete v0.4 se entrega como ZIP de PREPARACIÓN en ChatGPT. NO es instalable hasta que el usuario aporte desde su propio equipo una copia compatible de la carpeta `Promisory` original.

- Cada IA tiene su `.ai`, `.per` y `.py` con su mismo nombre.
- Un `morlet_router.py` común es el punto central. Por defecto usa un único modelo de LM Studio (Granite si la selección es inequívoca), no siete instancias.
- `.per` ni `.ai` **pueden abrir un proceso `.py`**. Python se inicia desde PowerShell/Windows y utiliza el puente Agent Bridge v3 de AoE2Control cuando está instalado y autorizado.
- Los 7 `.per` apuntan a `Morlet7_NOMBRE_Core/` en vez de `Promisory/`. Son 7 carpetas distintas para que la IA HD original del juego no cambie.
- `aoe2/preparar_promisory_aislado.py` es el preparador independiente que comprueba `defaultConstants`, `finalingConstants` y `finaling` y copia los includes, sin modificar `Promisory` original.
- En el ZIP el equivalente es `IA/preparar_nucleos.py`, que se ejecuta sobre la extracción local antes de copiar al directorio del juego.
- Si no hay Agent Bridge, sigue existiendo el motor `.per` nativo (si se han instalado correctamente los núcleos); nunca fingir integración Python.

Documentación detallada: [AOE2_ROUTER_PROMISORY_V04.md](../docs/AOE2_ROUTER_PROMISORY_V04.md).

**No están implementados en v0.4:** inferencia real de Qwen3-0.6B en NPU, acceso a SmolLM2 compartido desde el router, arranque automático del Python desde `.per`, ejecución dentro de AoE2 verificada o 500 frases por IA.
