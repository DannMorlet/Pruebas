# Historial de experimentos de Fresita

El panel Experimentos dibuja loss de entrenamiento y eval_loss de validación
sobre el número real de pasos, sin crear valores simulados.

Archivos locales:
- metricas_historial.jsonl: solo paso, loss y eval_loss, emitidos por TrainerCallback.
- metricas_validacion.json: evaluación final, si se configuró validación.

Usa Actualizar experimentos para leer datos; no hay sondeo constante.
Los datos de entrenamiento y las muestras no se escriben en el historial.

Interpretación: si la pérdida de entrenamiento baja mientras la de
validación sube, puede haber sobreajuste. La perplejidad no es una
precisión porcentual ni demuestra calidad universal.

CI prueba el filtrado de métricas y empaquetado x64. Falta validar
entrenamiento CUDA real en la RTX 5060 de 8 GB.
