# Evaluación offline de calidad · Fresita Studio

Evalúa **predicciones ya generadas** sin cargar modelos, descargar pesos ni ejecutar código. La pestaña **Evaluar IA** importa un JSONL con un objeto por línea:

    {"categoria":"es_mx","referencia":"¿Qué onda?","prediccion":"¿Qué onda?"}
    {"categoria":"codigo_python","referencia":"print(1 + 1)","prediccion":"print(2)"}

El ejemplo es sintético. No subas datos privados al repositorio.

## Métricas
- Español MX: coincidencia exacta normalizada (Unicode NFKC, minúsculas y espacios) y F1 de tokens. Los acentos no se eliminan. No equivale a evaluar naturalidad mexicana.
- Python: coincidencia textual y sintaxis mediante ast.parse, sin ejecutar el código. No mide corrección funcional.
- Total: proporción de coincidencias exactas entre categorías, sólo descriptiva.

Se guardan en Documentos/Fresita Studio/experiments/evaluaciones reportes JSON con métricas agregadas, SHA-256 del archivo y conteos. No contienen preguntas, referencias ni predicciones. El archivo original no se modifica. Límites: 8 MB, 5,000 filas y 20,000 caracteres por campo.

Para evaluar un modelo real, primero genera sus respuestas sobre un conjunto independiente y después importa ese JSONL. Fresita no afirma haber ejecutado inferencia ni entrenamiento.

Ejecución por consola:

    py -3.12 fresita_quality.py .\mis-predicciones.jsonl --guardar-en "$HOME\Documents\Fresita Studio"
