# 🍓 Fresita Studio · MVP Windows x64 en GitHub

Esta carpeta incluye **código ejecutable real** del primer MVP alojado en GitHub.
Interfaz en español mexicano, sin dependencias de IA para abrirla.

## Capacidades de este MVP
- Panel oscuro con acento rosa fresa.
- Importar datos JSON, JSONL, CSV, TXT; limpiar duplicados sin sobrescribir.
- Auditar ejemplos inválidos/duplicados y separar de forma reproducible 90/10 para futura validación, sin mezclar conjuntos.
- Inspeccionar cabeceras safetensors sin cargar la GPU.
- Guardar recetas de proyectos.
- Lanzar LoRA / QLoRA con PEFT/TRL desde un entorno Python separado y ver logs.
- Monitor de GPU mediante nvidia-smi, cuando está disponible.
- GitHub Actions compila en Windows 2022 x64 un Fresita.exe autónomo para la GUI.

**El entrenamiento CUDA NO está validado en RTX 5060 física.** QLoRA requiere
instalar bitsandbytes por separado y comprobar soporte de CUDA.

## Cómo abrir y ejecutar
Desde una copia local de esta carpeta:
```powershell
py -3.12 fresita.py
```

Para habilitar entrenamiento configura Python 3.12 x64 y un venv en
`%USERPROFILE%\Documents\Fresita Studio\.venv`:
```powershell
py -3.12 -m venv "$HOME\Documents\Fresita Studio\.venv"
& "$HOME\Documents\Fresita Studio\.venv\Scripts\python.exe" -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cu132
& "$HOME\Documents\Fresita Studio\.venv\Scripts\python.exe" -m pip install -r requirements-train.txt
```
Este ejemplo de CUDA debe contrastarse con la versión de controlador y wheels disponibles;
si no existe una wheel apropiada, no fuerces la instalación.

## CI y artefacto
La rama `feature/fresita-studio` activa el workflow con pruebas y empaquetado x64.
El artefacto aparece en Actions **si la ejecución terminó correctamente**.
No se modifica el repo `Manguito` ni otros proyectos.

## Alcance
Este MVP de GitHub es deliberadamente pequeño y no contiene aún el panel avanzado
completo v0.3 preparado aparte. Tampoco entrena cuatro estudiantes de 600M,
ni una red de 1000 agentes; esos son objetivos a desarrollar y validar.

## Auditoría y separación de datasets
En **Datasets**, selecciona un JSONL normalizado. La auditoría cuenta filas válidas, inválidas y duplicadas, y calcula longitudes sin enviar datos a la red. La separación 90/10 genera archivos independientes y reproducibles (mínimo 10 ejemplos únicos), conservando intacto el original. La GUI selecciona el conjunto de entrenamiento; el de validación queda guardado localmente. **Aún no se calcula una métrica del modelo sobre ese conjunto**. No uses el archivo de validación para entrenar si quieres evaluar generalización.

## Validación real de LoRA/QLoRA (opcional)
En **Entrenar**, selecciona dos archivos JSONL normalizados distintos: entrenamiento y validación.
La aplicación comprueba que no haya ejemplos repetidos entre ambos (ignorando mayúsculas y espacios)
y nunca usa el conjunto de validación para actualizar los pesos. Si se proporciona validación,
el worker calcula `eval_loss` durante el entrenamiento y una evaluación final. Guarda
`metricas_validacion.json` junto al adaptador con pérdida, perplejidad, pasos y número de
muestras, **sin texto privado**. La perplejidad es una medida dependiente del tokenizador,
no un porcentaje de precisión ni una prueba de calidad universal. Sin archivo de validación,
se conserva el entrenamiento anterior y no se inventan métricas.

Las pruebas CI validan la lógica de separación y el reporte; no ejecutan PyTorch/CUDA ni
comprueban la compatibilidad de los modelos en la RTX 5060 física.

## Gráficas de experimentos
El panel Experimentos dibuja loss y eval_loss por paso desde eventos reales de TRL, sin datos simulados. Lee el historial local sin prompts ni textos privados. Más detalles en docs/EXPERIMENTOS.md.

## Comparar experimentos (nuevo)

En **Experimentos** selecciona dos trabajos y pulsa **Comparar dos experimentos**.
Fresita compara `eval_loss` y superpone las curvas de validación únicamente
cuando coinciden las huellas SHA-256 del mismo archivo de validación y
tokenizador, longitud de secuencia y número de ejemplos. Los experimentos
anteriores sin estos metadatos no se consideran comparables. Los reportes
contienen huellas y métricas, nunca textos de entrenamiento.


## Evaluar respuestas de IA sin ejecutar código

La pestaña **Evaluar IA** recibe un JSONL de predicciones ya generadas y calcula coincidencia exacta normalizada y F1 de tokens para español mexicano, además de coincidencia textual y sintaxis de Python mediante análisis AST. No carga modelos ni ejecuta el código evaluado: **sintaxis válida no implica corrección funcional**. Los reportes incluyen sólo métricas agregadas y SHA-256 del archivo, sin preguntas ni respuestas privadas. Consulta [docs/EVALUACION_CALIDAD.md](docs/EVALUACION_CALIDAD.md) para el formato y las limitaciones.

## Generar predicciones locales y evaluarlas

En **Evaluar IA**, Fresita ahora permite generar respuestas con un servidor OpenAI-compatible en `127.0.0.1` y evaluarlas. Sólo envía las preguntas (no referencias) y requiere confirmación. Los JSONL de predicciones contienen textos privados y permanecen en el equipo. [Guía y límites](docs/PREDICCIONES_LOCALES.md). El servidor y el modelo deben estar iniciados por el usuario. CI usa un servidor falso, no CUDA.

## Medición de recursos durante inferencia (2026-11-01)
En **Evaluar IA**, el benchmark local registra línea base y pico observado de VRAM global de GPU 0 (nvidia-smi) y RAM global de Windows, sin sondeo permanente. No mide el consumo exclusivo del modelo ni garantiza capturar picos breves. Cuando falta una fuente, muestra N/D. El reporte numérico no contiene preguntas ni respuestas. Véase [docs/VELOCIDAD.md](docs/VELOCIDAD.md).


## VRAM por PID (experimental)
La pestaña **Evaluar IA** admite el PID opcional del proceso que ejecuta el
servidor local. Muestra la VRAM de ese proceso en GPU 0 sólo cuando
`nvidia-smi` devuelve una fila numérica inequívoca; de lo contrario N/D,
especialmente bajo WDDM. No es VRAM exclusiva del modelo. Consulta
[docs/VELOCIDAD.md](docs/VELOCIDAD.md). CI valida parsing, muestreo y
privacidad con datos falsos, no el hardware real.

## Evidencia de procesos de cómputo NVIDIA (experimental)
La detección de PID ahora diferencia **enumerado en la lista de cómputo de GPU 0**
de **VRAM numérica disponible**. Bajo WDDM un PID puede aparecer con VRAM N/D.
Si un PID no aparece, Fresita muestra «no confirmado», nunca «no usa GPU».
Una coincidencia sólo confirma que `nvidia-smi` enumeró el PID en esa consulta:
no identifica automáticamente el proceso que contiene los pesos ni prueba
uso exclusivo de la GPU. El análisis es puntual y no lee datos privados.


## Diagnóstico previo de CUDA (sin descargar modelos)
Antes de cargar pesos, el worker comprueba Python x64, dependencias instaladas,
disponibilidad de CUDA y VRAM total detectada. Para QLoRA exige `bitsandbytes`;
que esté instalado **no garantiza** que funcione con el controlador y la versión
de PyTorch. Si falta una dependencia, falla antes de descargar el modelo.
El diagnóstico devuelve versiones, nombre de GPU, VRAM total y, si PyTorch lo permite,
**VRAM libre observada** en GPU 0 (`vram_libre_mib`). Si CUDA/WDDM no permite
consultarla o devuelve datos inválidos, informa N/D sin impedir el diagnóstico.
La cifra libre es una **instantánea del dispositivo**, no memoria exclusiva del modelo
ni garantía de que el entrenamiento quepa en VRAM. Menos de 2 GiB libres genera
una advertencia, no un bloqueo. No lee datasets ni guarda secretos.

Desde el entorno de entrenamiento, crea un archivo de configuración JSON
con `{"qlora": false}` (o `true` para QLoRA) y ejecuta:
```powershell
& "$HOME\Documents\Fresita Studio\.venv\Scripts\python.exe" workers/train_lora.py --config receta.json --preflight
```
Este comando no entrena ni carga pesos. Si pasa, aún falta validar un
entrenamiento pequeño y el consumo real en la RTX 5060 de 8 GB.

## Checkpoints opcionales de entrenamiento (sin reanudación automática)
En **Entrenar**, activa «Guardar checkpoints cada 25 pasos (máximo 2)» si quieres
conservar estados intermedios de TRL. La opción está **desactivada por defecto**
para evitar gasto adicional de disco y RAM/VRAM. En una receta JSON, el campo
`checkpoint_interval` acepta 0 (desactivado) o un entero entre 1 y `steps`.
Cuando está activo, TRL guarda periódicamente checkpoints bajo la carpeta de
salida del experimento y conserva como máximo dos; el entrenamiento también
guarda el adaptador final. El guardado puede necesitar espacio considerable
y no se ha validado aún con CUDA física ni con todas las versiones de TRL.
La reanudación **explícita** está disponible desde «Seleccionar carpeta checkpoint-N»;
requiere un manifiesto creado por Fresita y validaciones previas. No se ha probado
todavía la recuperación real del estado del optimizador en una RTX 5060.
No se modifica el modelo base ni se suben pesos a GitHub.

## Diagnóstico de errores de memoria durante LoRA/QLoRA
Si la carga del modelo, preparación, entrenamiento o evaluación fallan por un error
reconocible de **VRAM CUDA**, Fresita emite una línea `FRESITA_DIAGNOSTICO`
con etapa, código `CUDA_SIN_VRAM` y pasos de recuperación en español.
Si Python informa `MemoryError`, indica `RAM_AGOTADA`. No reintenta ni
modifica automáticamente la receta, la longitud de contexto o los pesos.
El diagnóstico no incluye rutas ni textos privados; el traceback estándar del
worker sigue disponible para depuración **sólo en el equipo local**.
Una prueba CI con errores simulados no valida la recuperación física de CUDA.


## Reanudar desde un checkpoint (experimental, requiere GPU física)
En **Entrenar**, activa el guardado de checkpoints y usa **Seleccionar carpeta checkpoint-N** para reanudar un trabajo interrumpido. Mantén **idénticos** el modelo, LoRA/QLoRA, rango, tasa de aprendizaje, pasos, intervalo de guardado y archivos de entrenamiento/validación. Fresita valida la huella SHA-256 de la receta y el contenido de ambos datasets antes de iniciar la carga del modelo, y comprueba que el checkpoint seleccionado pertenezca a la carpeta de salida, tenga un número de paso coherente y contenga el estado de Trainer, optimizador, scheduler y RNG. También exige `adapter_config.json` con tipo LoRA y rango compatible, además de `adapter_model.safetensors` no vacío. Rechaza enlaces simbólicos en estos archivos. Esto comprueba la presencia y coherencia mínima, **no** la integridad criptográfica de los pesos ni la seguridad de cargar archivos PyTorch de origen desconocido. No busca checkpoints automáticamente ni sobrescribe una carpeta existente al iniciar un trabajo nuevo con guardado.

Sólo los trabajos nuevos con checkpoints habilitados generan el archivo local `fresita_checkpoint_manifest.json`. **Los checkpoints antiguos sin manifiesto se rechazan**; no se inventa compatibilidad. El manifiesto guarda una huella, no rutas ni textos del dataset. Se valida la identidad declarada del modelo, **no** la revisión remota ni el contenido de sus pesos: para reanudación fiable utiliza una copia local fija o una revisión inmutable. No se verifica aún que TRL/PEFT reanuden correctamente en tu RTX 5060; CI sólo prueba la validación y el empaquetado, no CUDA.

Para usarlo desde la receta JSON, añade `"resume_checkpoint": "C:\\\\ruta\\\\salida\\\\checkpoint-25"` y conserva `output` apuntando a la carpeta `salida`. La reanudación es explícita; si hay cualquier incompatibilidad se detiene con error antes de iniciar el entrenamiento.

## Motor llama.cpp CUDA 13.4 / CUDA Toolkit 13.4.3

En **Motor llama.cpp**, Fresita obtiene desde la API de GitHub la compilación
**más reciente** de llama.cpp para Windows x64 que incluya los archivos del
motor y del runtime NVIDIA CUDA 13.4. La descarga ocurre sólo por elección
explícita; compara tamaño y SHA-256 de ambos ZIP oficiales antes de extraer.
Conserva versiones anteriores para recuperación, sin instalar drivers ni
cambiar otras aplicaciones.

La versión más reciente comprobada al preparar la función fue **b12048**
(pre-release del 2 de noviembre); la última estable **v0.8.0** no publica
los ZIP CUDA 13.4 necesarios. Para cargar un GGUF, selecciona el archivo
desde la pestaña y abre `llama-server` en 127.0.0.1:8080.

**Entrenamiento PyTorch != runtime llama.cpp:** PyTorch 2.14.1 publica
ruedas oficiales `cu132` para Windows/Linux; al comprobar no encontré
`cu134` oficial. El ejemplo cu130 anterior pasó a cu132.
No se actualiza PyTorch automáticamente ni se presume que LoRA/QLoRA
funcione hasta probarlos. CUDA Toolkit 13.4.3 es la última edición de NVIDIA,
pero el runtime distribuido con llama.cpp usa CUDA 13.4.
Ver [documentación técnica](docs/LLAMA_CUDA.md).

## Búsqueda automática de actualizaciones del motor (2026-11-02)

Fresita comprueba **al abrir** si GitHub publica una build de llama.cpp
Windows x64 CUDA 13.4 más reciente que la instalada. Es una consulta
en segundo plano: la GUI abre sin esperar a la red. La casilla
**«Buscar actualizaciones al abrir Fresita»** permite desactivarla.

Las preferencias se guardan localmente en
`Documentos/Fresita Studio/config/actualizaciones.json` y no contienen
datos privados. Si GitHub no responde, no aparece un diálogo invasivo
ni se cambia el motor instalado. La descarga e instalación **nunca son
automáticas**: requieren pulsar el botón y confirmar. No se actualizan
PyTorch, drivers NVIDIA, CUDA Toolkit, Unsloth, TRL ni PEFT.

Si ya tienes la build más reciente, el botón no vuelve a descargarla.
El gestor mantiene intactas las versiones anteriores. Las pruebas CI
simulan preferencias y versiones; **no prueban una instalación física
de CUDA 13.4 en una RTX 5060**.

## Diagnóstico desde la interfaz (sin entrenar)

En **Entrenar**, pulsa **Revisar CUDA, PyTorch, TRL y PEFT (sin entrenar)**.
Fresita abre el worker en el entorno local `.venv` con la opción
`--preflight` y una receta temporal que sólo indica LoRA/QLoRA.
Muestra Python x64, paquetes instalados, GPU y VRAM observada, además de
errores y advertencias en español mexicano. La consulta corre en segundo
plano; **no descarga modelos, no lee datasets, no instala dependencias ni
inicia un entrenamiento**. Si falta el entorno Python, explica cómo
prepararlo. El resultado es un diagnóstico previo, no una prueba real
de entrenamiento ni de compatibilidad de bitsandbytes en tu RTX 5060.

Las pruebas de CI usan un proceso simulado y no requieren PyTorch/CUDA.

## Preparación guiada de dependencias (2026-11-02)

En **Entrenar**, pulsa **Preparar entorno de entrenamiento** para instalar
desde la propia GUI un entorno Python **nuevo**. Requiere el lanzador
`py -3.12` ya instalado en Windows. Tras confirmar, Fresita crea
`Documentos/Fresita Studio/.venv`, instala **PyTorch 2.14.1 cu132**
desde el índice oficial de PyTorch y las dependencias de
`requirements-train.txt` (TRL, PEFT, Transformers, etc.) desde PyPI.
Para el modo QLoRA agrega `bitsandbytes`, sin prometer que funcionará
con todas las combinaciones de GPU y driver.

**No** instala Python 3.12, controladores NVIDIA, CUDA Toolkit ni Unsloth.
Unsloth sigue siendo un módulo opcional pendiente de una matriz de
compatibilidad validada para Windows nativo. El gestor rechaza un `.venv`
existente y nunca lo sobrescribe. Si falla o se cancela una instalación
recién creada, intenta revertir únicamente esa carpeta, dejando intactos
datasets, checkpoints y pesos. Si Windows mantiene archivos bloqueados,
puede quedar una carpeta marcada para revisión manual.

Se ejecuta en segundo plano, con cancelación y mensajes por etapa sin
mostrar datos privados. Después de instalar, usa el botón de diagnóstico
para verificar CUDA; **CI no prueba descargas reales ni entrenamiento GPU**.
PyTorch cu132 y llama.cpp CUDA 13.4 son entornos independientes.
Referencia oficial: https://pytorch.org/get-started/previous-versions/
