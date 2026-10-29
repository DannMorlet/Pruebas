# Gaming · Especificación UX v0.1

Estado: diseño, no app instalada. Inspiración: ChatGPT Codex/Work + LM Studio, con identidad propia.

## Nombres
- Gaming: producto y ventana.
- Matick: asistente principal.
- Local: selección de modelo y conexiones con LM Studio/MCP.
- Morlet: espacio central de proyectos y chats.

## Layout adaptable
- Sigue posición y tamaño de ventana de LM Studio.
- Panel izquierdo y panel derecho pueden abrirse, cerrarse, acoplarse o desacoplarse; el contenido central refluye de inmediato.
- En pantalla pequeña colapsa botones secundarios y conserva editor, conversaciones y estado.
- Compatible con dos monitores verticales y escalas DPI distintas: las posiciones reales y el DPI deben medirse, no suponerse.
- Alternativa si el acoplamiento nativo no es posible: ventana compañera o flotante, sin inyección en LM Studio.

## Encendido
- Interruptor OFF por defecto. Sin inferencia, captura, servidor adicional ni tareas recurrentes mientras OFF.
- ON activa solo funciones solicitadas. Al cerrar, liberar conexiones y recursos. Evitar instancias duplicadas.

## Historial
- Nuevo chat, buscar, fijar, renombrar.
- Vaciar chat actual, borrar individual, seleccionar y borrar por lotes y eliminar todo con confirmación.
- Solo borrar historial de Gaming, nunca chats propios de LM Studio o ChatGPT.
- Soporte de exportación y almacenamiento paginado local.

## Rendimiento
- Cero captura continua cuando no se usa.
- Evitar duplicar motor Chromium, preferir UI nativa.
- Medir y documentar RAM/CPU, fugas, latencia de resize y cierres; problema anterior reportado de ~1 GB RAM no puede considerarse resuelto sin pruebas.

## Adaptación específica a pantallas verticales

- Ventana redimensionable horizontal y verticalmente, con tamaño mínimo razonable y sin relación de aspecto fija.
- La composición debe responder a cambios del rectángulo real, no a resolución de pantalla predefinida.
- Para anchuras estrechas, lateral izquierdo compacto y panel derecho como overlay/desacoplado; el chat y compositor conservan prioridad.
- Al arrastrar entre monitores, tratar DPI diferente, cambio de monitor, maximizar/restaurar y arrastrar esquinas sin congelar la ventana.
- El [prototipo HTML](../prototype/index.html) permite comprobar visualmente modos horizontal, vertical, compacto y libre; no implementa todavía seguimiento Win32 del proceso LM Studio.
