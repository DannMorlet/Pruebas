# Benchmark de latencia y tokens por segundo (experimental)

Fresita puede medir un modelo local compatible con OpenAI usando el script
fresita_speed.py. El panel gráfico todavía no incorpora esta medición.

Ejemplo con Python 3.12 desde FresitaStudio:

    py -3.12 fresita_speed.py casos.jsonl --modelo modelo-cargado

El archivo casos.jsonl tiene las claves pregunta, referencia y categoria,
igual que el benchmark de calidad existente. Solo se envía pregunta al
servidor 127.0.0.1. No se envía referencia.

Se guardan predicciones privadas para posterior evaluación y un reporte
numérico independiente bajo Documents/Fresita Studio/experiments/velocidad.
El reporte no contiene prompts, referencias ni respuestas. Si el servidor
no reporta usage.completion_tokens, Fresita muestra N/D en lugar de
inventar tokens por segundo.

La tasa calculada es tokens de salida / duración total de solicitudes.
Incluye latencia HTTP y prefill; no representa velocidad pura de
decodificación. La medición no cuantifica ni atribuye VRAM a un proceso.
El servidor debe estar iniciado manualmente. No se ejecuta código
Python generado por el modelo. Las pruebas CI usan un requester falso.
