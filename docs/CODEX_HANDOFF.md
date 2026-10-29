# Gaming · Plan de implementación para Codex

Este documento describe requisitos y no acredita que exista una integración funcional.

## Paso 1 — auditoría
- Confirmar versión LM Studio, rutas reales, modelo cargado, monitor principal y escalas.
- Respaldar archivos MCP y datos antes de modificar nada.
- Revisar chat_server.mcp y chat_server.py; identificar el fallo previo sin borrar el proyecto.

## Paso 2 — interfaz
- Construir UI oscura Gaming; áreas Matick, Local y Morlet.
- Probar ventana propia acoplada de forma visual al contenido libre de LM Studio.
- Validar izquierdo abierto/cerrado, derecho abierto/cerrado y ventana compacta; dos monitores y DPI mixto.
- Ofrecer desacoplar/manual si el rectángulo del contenido de LM Studio no puede conocerse de forma fiable.

## Paso 3 — control y chat
- OFF al inicio, no procesos en segundo plano. ON manual, evitar duplicados; parada limpia.
- Conversación con el modelo realmente cargado sin autoload.
- Borrar chats individual y por lotes, vaciar conversación o todo el historial local, con confirmaciones y pruebas.
- Streaming, cancelación y manejo de pérdida de conexión.

## Paso 4 — rendimiento
- Perfil de RAM/CPU y pruebas de estrés de resize, cierres, encendido repetido, grandes historiales.
- Investigar aumento de RAM reportado (~1 GB). No prometer cifras sin medición.
- No alterar configuración MCP existente hasta tener pruebas y respaldo; pruebas por cada herramienta.

## Criterios de aceptación
- La ventana sigue el layout sin tapar controles nativos.
- OFF significa ninguna ejecución iniciada por Gaming.
- Chats se eliminan solo donde el usuario lo confirmó.
- MCP originales preservados; restauración probada.
- Medidas de memoria/CPU documentadas.

Nomenclatura: Gaming (marca), Matick (asistente), Local (motor), Morlet (entorno). No usar nombres anteriores para la marca.
