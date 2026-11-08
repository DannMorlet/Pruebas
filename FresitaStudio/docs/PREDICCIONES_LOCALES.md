# 🍓 Predicciones automáticas locales y evaluación de calidad

En la pestaña **Evaluar IA** puedes generar predicciones mediante una API compatible con OpenAI
que se ejecute **en tu propio equipo**, usando sólo `http://127.0.0.1:PUERTO/v1`.
El motor es opcional (p. ej. servidor local LM Studio o Matick compatible), no es parte de Fresita.
Fresita no arranca ni descarga modelos por sí sola.

## Archivo de entrada JSONL

Una pregunta por línea, con `categoria`, `pregunta` y `referencia`:

```jsonl
{"categoria":"es_mx","pregunta":"Saluda de forma breve en español mexicano","referencia":"¡Qué onda!"}
{"categoria":"codigo_python","pregunta":"Escribe una función suma(a,b) en Python","referencia":"def suma(a, b):\n    return a + b"}
```

Son ejemplos ficticios; no subas datos privados a GitHub. La referencia **nunca se
envía al servidor**: sólo se transmite `pregunta` y el identificador del modelo.
La conexión es exclusivamente loopback (127.0.0.1), HTTP sin redirecciones ni proxies.

En el panel, introduce el identificador exacto del modelo cargado en tu servidor,
selecciona el JSONL y pulsa **Generar predicciones y evaluar (local)**.
Requiere confirmación explícita. Se procesan hasta 100 casos por lote,
con `temperature=0` y `max_tokens=256` (determinismo sujeto al motor).

Al terminar se guarda un JSONL privado con `categoria`, `referencia` y
`prediccion` en `Documentos/Fresita Studio/experiments/predicciones/`.
**No subas este JSONL a GitHub ni lo compartas**. El reporte agregado en
`experiments/evaluaciones/` no contiene textos. Si hay un error o se cancela,
no queda un JSONL final parcial. La cancelación espera la solicitud HTTP en curso
(hasta 45 segundos), y la evaluación no se inicia sola.

También puede usarse por consola:
```powershell
py -3.12 fresita_predict.py .\mis-preguntas.jsonl --modelo "ID-exacto-del-modelo" --endpoint http://127.0.0.1:1234/v1
```

## Límites y verificaciones

- Hasta 8 MB y 100 preguntas, 4,000 caracteres por pregunta, 20,000 por referencia/respuesta.
- La evaluación offline calcula coincidencia, F1 de tokens y sintaxis AST. No ejecuta código ni certifica calidad o corrección.
- Las pruebas CI usan un servidor HTTP falso local. **No prueban** un modelo real ni CUDA.
- El proceso de inferencia usa el modelo que el usuario haya cargado; su VRAM se mide aparte.
