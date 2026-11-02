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
& "$HOME\Documents\Fresita Studio\.venv\Scripts\python.exe" -m pip install torch --index-url https://download.pytorch.org/whl/cu130
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
