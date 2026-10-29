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
