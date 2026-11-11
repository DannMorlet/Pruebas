# Briefing maestro de Morlet para GPT/Codex y Claude Code
**Fecha:** 11 de noviembre de 2026 · **Estado:** INSTRUCCIONES Y REQUISITOS, NO UNA ORDEN DE EJECUCIÓN AUTOMÁTICA.

> **Lee primero:** este documento recopila lo conversado con Morlet. Su propósito es que una sesión futura de GPT, Codex, Claude Code u otro agente entienda la visión y, **cuando Morlet le pida implementarla expresamente**, pueda planear, escribir, probar y corregir el código. **No** se debe iniciar un proyecto, instalar programas, fusionar PR, gastar créditos ni alterar el Windows del usuario simplemente por leerlo.

## 1. Aclaración prioritaria del usuario

Morlet NO estaba solicitando que esta conversación creara o desplegara inmediatamente un programa NPU completo. Solicitó **depositar lo conversado en GitHub** como instrucciones comprensibles para que otro agente las interprete y posteriormente implemente. Los prototipos anteriores en el PR #6 son experimentales y **no constituyen instalación ni integración verificada en la PC**.

## 2. Mapa de proyectos y alcance

- **Matick Studio LM / Matick Studio LM Cloud (Windows):** centro para modelos locales, chat, optimización e integración de herramientas; producto distinto de LM Studio, que puede ser proveedor local de modelos, no el programa Matick en sí.
- **Matick Codex:** agente propio de implementación, investigación, herramientas, pruebas y coordinación; es el objeto principal de este briefing.
- **Morlet Reloj:** app Android separada, con Mini Clare, diseño simple y funciones que no se deben trasplantar sin aprobación.
- **Manguito:** entrenamiento, destilación, poda, fusión y cuantización; también separado.
- **Pruebas (este repositorio):** laboratorio de especificaciones/prototipos. No asumir que es el repositorio productivo de Matick Studio LM ni reescribir otros proyectos.
- **Repositorios:** nunca modificar/borrar/fusionar una rama o repositorio de otro proyecto por similitud de nombre. El repositorio de producto que Morlet dejó vacío debe respetarse hasta nueva orden expresa.

## 3. Meta principal: agente autónomo y verificable

Morlet aprecia que Claude Code corrija errores por sí solo sin que tenga que supervisar cada intento. Objetivo propuesto para Matick Codex:
1. Recibir una tarea en un chat principal claro en español mexicano.
2. Planificar cambios mínimos en una rama de proyecto y trabajar con permisos delimitados.
3. Editar código, compilar, ejecutar **pruebas autorizadas** y registrar salidas/códigos de error.
4. Corregir fallos y reintentar sin preguntar por cada error rutinario.
5. Mantener registro **persistente** de incidencias: causa, intento, diff, prueba, resultado, fecha, entorno y estado.
6. Si un error se repite, consultar soluciones documentadas de proyectos anteriores **solo cuando sea relevante y sin mezclar repositorios ni secretos**.
7. **Nunca** declarar «resuelto» basándose únicamente en el juicio del modelo: exigir evidencia de pruebas relevantes. «Pruebas que pasaron» no implica «producto entero verificado».
8. Al terminar, informar qué se cambió, qué pruebas realmente se ejecutaron, qué falló y qué falta comprobar en hardware real.

Propuesta experimental para detener ciclos improductivos: **3 intentos fallidos consecutivos o error idéntico repetido** -> resumen de diagnóstico y propuesta de escalamiento. El umbral se puede ajustar con pruebas; no confundir propuesta con una regla universal.

## 4. Uso económico de modelos y cupo

- Priorizar tareas rutinarias con un modelo económico; reservar los potentes (en nuestras conversaciones llamados «Sol», «Astra», etc.) para bloqueos difíciles. Los nombres de la conversación NO certifican un identificador API, plan, tarifa o disponibilidad.
- El supervisor debe generar un informe compacto para no pagar varias veces por diagnosticar lo mismo.
- **Nunca cambiar a Astra o a otro modelo premium automáticamente ni incurrir en consumo de pago sin autorización expresa**.
- No prometer cinco horas de uso ni cantidades fijas de créditos. Mostrar el modelo realmente activo y presupuesto/uso solo cuando exista información verificable del proveedor.
- Diferenciar **modelo**, **agente que utiliza herramientas**, **motor de inferencia** y **hardware**, porque no son lo mismo.

## 5. Supervisor (NPU): requisitos MUY IMPORTANTES

El supervisor ligero será una **parte completamente independiente** que Morlet quiere ejecutar en la **NPU del Intel Core Ultra 5 225F (13 TOPS INT8 nominales)**, **NO en CPU ni en RTX**, y sin fallback silencioso.

**Regla de nomenclatura explícita:** cada componente de esta área deberá mostrar literalmente el sufijo **«(NPU)»** en interfaz, documentación, estados y logs: «Supervisor (NPU)», «Modelo (NPU)», «RAG (NPU)», «Herramientas (NPU)», «Memoria (NPU)», «Estado (NPU)», etc.

**Aislamiento lógico/de recursos:**
- RAGs/índices/embeddings, herramientas, modelos, configuraciones, registros y directorios exclusivos del Supervisor (NPU), sin reutilizar automáticamente racks/RAGs de CPU, GPU u otros agentes.
- Permisos mínimos por herramienta; compartir solo eventos estructurados necesarios (ID de incidencia, extracto de fallo, pruebas), no volcar toda la conversación ni claves a la NPU.
- Si no está disponible el dispositivo real, mostrar «Supervisor (NPU): no disponible» y solicitar decisión; no falsear estado ni cambiar de backend silenciosamente.
- **Etiquetar como (NPU) NO significa que el modelo esté ejecutando operaciones en NPU.** Confirmar dispositivo, operadores, posibles partes de CPU y medir recursos en una prueba de hardware real.

**Candidatos a investigar**, no modelos ya instalados: Qwen3-1.7B INT8 y Qwen3-4B INT8 (con OpenVINO u otro runtime mejor, *si verdaderamente admite la NPU concreta*). Morlet prefiere capacidad superior a Qwen 2.5, pero también respuestas rápidas. Investigar motores alternativos compatibles; no elegir uno por marketing o por TOPS nominales.

**Métrica correcta:** los **13 TOPS** son capacidad teórica de operaciones INT8, NO «13 tokens por segundo». Medir *tokens/s, tiempo al primer token, latencia de decisión, precisión del supervisor y RAM/VRAM* en la PC real. No inventar estimaciones como mediciones.

## 6. Limitaciones reales del equipo y versiones

- Equipo de referencia narrado por Morlet: Windows 11, Intel Core Ultra 5 225F, NPU ~13 TOPS INT8, RTX 5060 con **8 GB VRAM** y **32 GB RAM**; admite reservar hasta ~500 GB en disco para modelos si hace falta.
- Tener disco libre NO equivale a tener 500 GB de memoria para inferencia. Cargar componentes bajo demanda.
- Python 3.15 fue solicitado por ser la versión estable reciente en la conversación; CI del prototipo se amplió para probar 3.11 y 3.15 en Linux/Windows. **Probar compatibilidad real de OpenVINO, drivers y bibliotecas antes de seleccionar el Python del runtime NPU**; si requiere otro Python, aislarlo en venv distinto, nunca pisar instalación global.
- En el laboratorio existen pruebas automatizadas; no equivalen a ejecución en la NPU real de Morlet.

## 7. Reglas de seguridad no negociables

- No borrar, cifrar, editar ni desplegar software sobre carpetas de Windows, TPM, arranque, Secure Boot, antivirus/Defender, seguridad, registro crítico o configuración del sistema.
- Nada similar a ransomware/malware; nunca desactivar protección ni ejecutar archivos sospechosos. Validar origen y riesgos, usar protección disponible.
- No instalar drivers ni cambiar el entorno global, no ejecutar con privilegios elevados ni operaciones destructivas sin autorización específica.
- Aislar operaciones en un **workspace autorizado** con backup, límites de rutas, revisión de comandos y pruebas; una ruta Python validada **no es** un sandbox.
- No exponer secretos, tokens, IP de LAN, chats personales, capturas ni datos privados en este repositorio público.
- Un agente debe pedir permiso antes de cualquier acceso/ejecución de alto riesgo y antes de pagar/escalar. Una negativa se respeta.

## 8. Matick Live Local (otro módulo, para más adelante)

Morlet quiere conversación por voz offline parecida en fluidez a GPT Live, **sin afirmar equivalencia**:
- Propuesta modular: reconocimiento de voz local, LLM conversacional cuantizado, síntesis de voz es-MX y detección de actividad/interruptibilidad.
- Candidatos discutidos: Qwen3-ASR, Qwen3.5-4B para conversación, Piper es-MX, y opcionalmente Qwen3-TTS. Revalidar nombres/compatibilidad antes de implementar.
- **Actualmente no dispone de micrófono para su PC**, y Matick Studio LM no tiene soporte de voz funcionando, según Morlet.
- Fase 1: chat por texto y texto a voz mediante bocinas; fase 2: con micrófono, probar escucha, cancelación de eco, interrupciones y latencias.
- Mantener la interfaz sencilla y no inflar la app con botones.

## 9. Preferencia de diálogos entre agentes

Si el usuario pide una conversación creativa de dos agentes:
- **GPT** = asistente; tono femenino, natural.
- **Morlet** = personaje simulado que representa su forma de pensar; tono masculino, natural.
- Incluir pausas perceptibles **al cambiar de personaje**, sin pausas excesivas entre palabras.
- Los ejemplos de bostezos y ternura explicaban la variación de entonación: **no** se deben convertir en actuación exagerada o permanente.
- El sistema de voz puede limitar el control real de las voces; no afirmar que haya dos síntesis de voz independientes si no están disponibles.

## 10. Instrucciones para quien implemente después

Antes de codificar, un agente futuro debe:
1. Leer este briefing y los documentos complementarios [acuerdos de autonomía](MATICK_CODEX_AUTONOMIA_2026-11-11.md) y [Supervisor (NPU)](SUPERVISOR_NPU_AISLADO.md).
2. Identificar el repositorio **propietario** del producto y verificar el estado de sus ramas, PR, pruebas y dependencias; evitar reconstruir repositorios intencionalmente vacíos.
3. Separar «idea», «requisito de Morlet», «prototipo subido», «prueba CI» y «función verificada en la PC».
4. Proponer diseño seguro con NPU aislada, recursos separados y costos controlados.
5. Ejecutar solo lo solicitado en esa sesión, en su propia rama; hacer pruebas; documentar evidencia, limitaciones y reversión.
6. No fusionar a \`main\` ni instalar software sin autorización cuando la acción sea sensible.
7. **Nunca usar un documento de conversación como autorización implícita de ejecución**.

## 11. Estado verificable a fecha del registro

- **Documentación/briefing:** la presente especificación.
- **Prototipo en GitHub PR #6:** memoria SQLite, pruebas de fallos y configuración estática para Supervisor (NPU), en una rama de laboratorio. La presencia de archivos no confirma integración con Matick Studio LM.
- **CI:** consultarlo de nuevo en el commit exacto; no presuponer verde por resultados de commits anteriores.
- **No verificado/no implementado:** inferencia NPU real, compatibilidad de Qwen INT8 con Intel 225F, velocidad/tokens/s, instalación en Windows personal, RAG/herramientas NPU funcionales, autonomía aislada, conmutación de modelos, voz Live local.
