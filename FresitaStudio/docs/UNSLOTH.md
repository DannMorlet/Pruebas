# Unsloth opcional: diagnóstico local y límites

**Fecha:** 2026-11-02. **Plataforma objetivo:** Windows 11 x64, RTX 5060 8 GB, 32 GB RAM.

La documentación oficial de Unsloth indica que Unsloth Core admite Windows
y GPUs NVIDIA RTX 50, pero requiere una combinación compatible de Python,
PyTorch, Triton, bitsandbytes y controladores. Véase:
- https://github.com/unslothai/unsloth
- https://docs.unsloth.ai/get-started/installing-+-updating/windows-installation

## Qué se implementó
En **Entrenar**, pulsa **Comprobar Unsloth opcional (sin instalar)**.
Fresita usa Python del entorno de entrenamiento ya existente y un proceso
aislado para leer versiones de paquetes instalados, la compilación CUDA de
PyTorch y la detección de GPU. No importa el paquete Unsloth, no descarga
pesos, no lee datasets, no instala paquetes ni modifica el entorno.

La presencia de un paquete no garantiza que los kernels Triton ni
Unsloth funcionen. Se informa claramente que el backend de entrenamiento
**sigue siendo TRL/PEFT**. No se ofrece una falsa opción de entrenamiento
Unsloth que sólo invoque el worker anterior.

## Qué falta para habilitarlo
1. Preparar un entorno Unsloth **independiente** del venv TRL/PEFT actual.
2. Validar instalación oficial en Windows con Python y PyTorch compatibles.
3. Probar importación de Unsloth y una carga pequeña en RTX 5060 real.
4. Integrar un worker Unsloth distinto, con cancelación, logs, checkpoints,
   pruebas de regresión y comparación con el worker TRL/PEFT.
5. Medir VRAM, tokens/s y calidad; no prometer ahorro sin medición.

La CI de Windows comprueba el parser y el comando de diagnóstico con
respuestas simuladas; **no importa Unsloth ni ejecuta CUDA**.
