# Motor llama.cpp oficial con NVIDIA CUDA 13.4

## Versiones verificadas (2 de noviembre de 2026)
- CUDA Toolkit más reciente de NVIDIA: **13.4.3** (octubre 2026).
- llama.cpp última release estable API: **v0.8.0** (28 octubre), sin binarios de Windows CUDA 13.4 adjuntos a esa release.
- llama.cpp nightly/pre-release más reciente al comprobar: **b12048** (2 noviembre 2026), con ZIP Windows x64 para CUDA 13.4 y runtime CUDA correspondiente.
- Fuente del motor: https://github.com/ggml-org/llama.cpp/releases
- Archivo CUDA official: https://developer.nvidia.com/cuda-toolkit-archive

## Implementación Fresita
La pestaña **Motor llama.cpp** obtiene dinámicamente la release más reciente
que tenga **ambos** paquetes oficiales Windows x64 CUDA 13.4.

El usuario debe pulsar explícitamente para descargar ~600MB. Fresita valida
**SHA-256 publicado por GitHub y tamaños**, evita extracción insegura y no sobrescribe
versiones anteriores. Los DLL del runtime y llama-server quedan versionados en
la carpeta local `Documentos/Fresita Studio/motores/llama/`.

**El instalador de llama.cpp no instala controladores NVIDIA ni CUDA Toolkit en
el sistema operativo.** Usa bibliotecas de runtime incluidas en artefactos oficiales;
el driver instalado debe ser compatible. CUDA 13.4 apunta a controlador R615
y posteriores para compatibilidad completa. `nvidia-smi` informa la versión de
CUDA máxima admitida por el driver, no necesariamente el Toolkit instalado.

Se puede seleccionar un GGUF y lanzar manualmente `llama-server`, siempre
ligado a 127.0.0.1:8080, con contexto inicial 2048 y 20 capas GPU. La cantidad
de capas se tendrá que ajustar según el modelo y la VRAM libre; no se garantiza
que cualquier GGUF quepa.

Al cerrar Fresita se finaliza únicamente el proceso llama-server iniciado desde
su propio panel. No mata servidores ajenos.

## PyTorch y entrenamiento
**No mezclar CUDA Toolkit 13.4.3 con la versión CUDA del wheel PyTorch.**
PyTorch dispone de sus propios binarios y dependencias CUDA. Seleccionar el wheel
que PyTorch publique oficialmente para Windows x64; no asumir que existe
`cu134`. No reinstalar ni sustituir un entorno de entrenamiento sano
simplemente por la versión de Toolkit.

## Validación
Tests unitarios CI comprueban selección de releases, rutas seguras, control
loopback y descubrimiento de versiones. No descargan ni ejecutan los ~600MB en CI.
Quedan pendientes pruebas de descarga, DLLs, arranque y generación con
un modelo GGUF en RTX 5060 física y driver compatible.
