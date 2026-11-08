# Guía de desarrollo para Fresita Studio

Estas instrucciones se aplican al directorio `FresitaStudio/`; es un proyecto **diferente** al Gaming de la raíz.

## Identidad y plataforma
- Nombre del programa: Fresita Studio; binario final `Fresita.exe`.
- Español mexicano claro, diseño oscuro, acentos fresa, sin controles falsos.
- Windows 11 x64, NVIDIA RTX 5060 8 GB VRAM, 32 GB RAM.
- El panel debe abrir sin cargar modelos pesados ni instalar PyTorch. No hacer polling permanente.
- No modificar repos de Manguito, Matick Cloud o Salud Bridge.

## Ingeniería
- Python 3.12 x64 recomendado para compatibilidad de entrenamiento; ejecutar GUI sin paquetes de ML.
- Separar GUI, núcleo y workers; cada proceso de entrenamiento debe poder cancelarse.
- Para Unsloth, detectar versiones compatibles antes de instalar: no asumir compatibilidad universal entre todos los modelos ni con Python 3.15.
- Guardar recetas JSON y logs, usar rutas locales seguras, proteger pesos originales y no borrar archivos del usuario.
- Una operación tiene estado: no disponible, listo, ejecutándose, completado o fallido.
- Las estimaciones de VRAM son aproximadas; medir ejecución real con GPU física.
- No declarar funcionalidad de edición o distilación automática hasta pasar pruebas reales.

## Secuencia recomendada
1. Migrar código de Fresita 0.1 y verificar tests.
2. Montar CI Windows x64: lint, tests, compilación y artefacto `Fresita.exe`.
3. Integrar datasets/SFT/LoRA/QLoRA con Unsloth como backend opcional.
4. Implementar DPO, destilación y edición de modelos con comprobación de arquitectura.
5. Añadir benchmarks, gráfico de pérdida, monitor GPU y gestión de experimentos.
6. Abordar estudiantes 600M y después entrenamiento multiagente Matick.

## Seguridad de GitHub
- Nunca incluir datos del usuario, .venv, modelos, checkpoints, GGUF, pesos o secretos.
- Trabajar en rama y PR; no fusionar sin comprobación de pruebas.
