# Supervisor (NPU) — aislamiento propuesto para Matick Codex

**Corrección solicitada por Morlet:** el supervisor debe ejecutarse **exclusivamente en la NPU** del Intel Core Ultra 5 225F. No confundirlo con CPU ni GPU. No está autorizado un cambio automático a CPU, GPU o nube. Si la NPU está indisponible o el modelo no funciona ahí, se muestra **«Supervisor (NPU): no disponible»** y se detiene esa función. Cualquier alternativa requiere aprobación explícita.

## Identificación en interfaz

Todo componente y aviso del supervisor debe terminar con **(NPU)**:
- Supervisor (NPU)
- Modelo (NPU)
- Herramientas (NPU)
- RAG (NPU)
- Historial (NPU)
- Estado (NPU)

Los demás motores de Matick Studio LM mantienen su identidad propia y recursos separados. Esta aclaración debe mostrarse en pantalla, logs y reportes, no solo al iniciar.

## Almacenamiento aislado

Propuesta de directorio de datos exclusivo del supervisor, configurable y **no compartido** con otros modelos:
```text
npu/
  modelos/
  herramientas/
  rag/
    documentos/
    indice/
  historial/
  configuracion/
```
El prototipo de configuración en este PR valida rutas y etiquetas; **no** instala herramientas, indexa documentos, migra un RAG ni ejecuta inferencia. Las carpetas de runtime solo se crearán tras decidir la ruta de datos local y dentro de ese directorio, sin tocar el sistema.

## Contrato entre supervisor y Matick Codex

- Entrada mínima: `issue_id`, resumen, diagnóstico/resultado de pruebas; **no** compartir conversaciones completas por defecto.
- Salida: propuesta, confianza calibrada, motivo y recomendación; las verificaciones reales de código siguen siendo obligatorias.
- No importar automáticamente herramientas, embeddings, bases vectoriales, memorias ni RAGs de CPU/GPU.
- Si el backend informa `CPU`, `GPU`, `AUTO` o `MULTI`, **rechazar la sesión** en vez de etiquetarla (NPU). Un nombre (NPU) por sí solo nunca acredita que el cálculo se realizó en la NPU.
- Modelo candidato: Qwen3-1.7B INT8; compatibilidad y tokens/s con la NPU del 225F **sin verificar en la computadora real**.
- Posible motor OpenVINO: debe comprobarse el dispositivo efectivo y los operadores/soporte del modelo. No declarar la NPU operativa solo por una configuración estática.

## Criterios pendientes para integración

1. Seleccionar una ruta local segura de almacenamiento para datos NPU.
2. Verificar disponibilidad de la NPU mediante el runtime, ejecutar inferencia y medir tokens/s y memoria de uso.
3. Comprobar efectivamente que no se produce fallback a CPU ni GPU durante inferencia, y documentar cómo se detecta y detiene.
4. Conectar selector de herramientas **solo (NPU)**, base de conocimiento y RAG (NPU) con permisos mínimos.
5. Mantener matriz de pruebas en CI. **No equivale a prueba de hardware NPU.**
