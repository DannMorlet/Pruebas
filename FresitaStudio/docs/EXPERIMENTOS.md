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

## Comparación de dos experimentos

Selecciona dos entradas en **Experimentos** y pulsa **Comparar dos experimentos**.
Fresita sólo muestra ganador de `eval_loss` si ambos reportes tienen
exactamente la misma huella SHA-256 del archivo de validación, la misma
huella de serialización del tokenizador rápido, igual longitud máxima de
evaluación y el mismo número de ejemplos. Si falta cualquier metadato
(como en experimentos anteriores), no declara ganador.

Los entrenamientos futuros guardan únicamente huellas SHA-256 y números;
no se guardan textos del dataset, rutas privadas ni vocabularios. La
comparación es orientativa: no mide exactitud en tareas ni calidad de
respuestas, y distintas versiones del modelo/tokenizador pueden alterar
los resultados. Si cambia el orden del JSONL, la huella cambia y se
rechaza la comparación por prudencia.

El gráfico superpone `eval_loss` de ambos experimentos cuando hay
historial disponible; no fabrica curvas ni reentrena modelos.
