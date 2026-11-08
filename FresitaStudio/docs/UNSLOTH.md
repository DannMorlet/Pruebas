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

## Instalación guiada en entorno independiente (2026-11-02)

**Nuevo:** botón **Preparar Unsloth aislado (experimental)** en Entrenar.
Sigue el procedimiento de Unsloth Core para Windows publicado en su
[README oficial](https://github.com/unslothai/unsloth): Python **3.13 x64**,
`uv venv`, instalación de **torchao primero** y
`uv pip install unsloth --torch-backend=auto`.

Requisitos previos: instalar Python 3.13 y `uv` por separado (Fresita no
los instala globalmente). Con autorización explícita, crea
`Documentos/Fresita Studio/.venv-unsloth` y descarga dependencias.
El entorno existente `.venv` de TRL/PEFT queda intacto. No descarga pesos
ni ejecuta scripts remotos mediante PowerShell. Comprueba dependencias con
`uv pip check`, importación de PyTorch, versión CUDA del wheel y metadatos
de paquetes; **no importa Unsloth ni ejecuta kernels**. Si falla o se cancela,
intenta retirar únicamente el entorno nuevo identificado por un marcador.
Nunca sobrescribe un entorno Unsloth ya existente.

Para comprobarlo pulsa **Comprobar Unsloth aislado (sin instalar)**. La
opción antigua comprueba `.venv` y se conserva. El entrenamiento de la GUI
continúa en `.venv` con TRL/PEFT, no se ha añadido un backend de entrenamiento
Unsloth sin validación real.

**Pendiente GPU física:** instalación completa de dependencias, importación
de Unsloth, prueba mínima CUDA/Blackwell, VRAM y reversión tras errores reales.
CI prueba planes y rollback con procesos simulados; no instala uv ni Unsloth.
