# Matick Codex — acuerdos de autonomía y seguridad (11 nov 2026)

**Estado:** acuerdo de diseño y prototipo aislado en `Pruebas`. No integrado a Matick Studio LM, LM Studio, Windows ni a las cuentas de modelos. No hay cambio automático de modelo implementado.

## Qué pidió Morlet

- El agente debe **implementar, compilar, leer fallos, corregir y reintentar** sin pedir instrucciones por cada error pequeño, como en la experiencia relatada con Claude Code.
- **No debe olvidar fallos** ni decir que arregló algo sin evidencia. Mantener memoria persistente y comprobar resultados.
- Usar el modelo de menor costo que pueda resolver la tarea; **ofrecer**, no activar, modelos más costosos en bloqueos difíciles. Los nombres hablados «Sol» y «Astra» son etiquetas conversacionales: comprobar nombres reales, selector, disponibilidad y costos antes de integrar proveedores.
- **Astra o cualquier modelo premium solo con autorización explícita**, con causa y resumen del error. La negativa no puede disparar una nueva solicitud automática.
- Para el modo de cinco horas, buscar ahorro de cupo; **no prometer duración ni créditos restantes**, porque dependen del servicio y el uso.

## Ciclo de reparación propuesto

1. Crear un identificador de incidencia (ej. `ui-chat-123`) y conservar contexto del trabajo.
2. Guardar en SQLite cada fallo, tipo de error, modelo utilizado y fecha; capturar artefactos mínimos de prueba con cuidado de no guardar secretos.
3. Proponer corrección pequeña y ejecutar únicamente pruebas autorizadas en el entorno de proyecto.
4. **Nunca** marcar terminado por la opinión del LLM. Una ejecución de pruebas con código de salida no cero, prueba ausente o timeout es un fallo.
5. Si hay **tres fallos consecutivos** o se repite exactamente un error: detener reintentos costosos y **recomendar** un especialista; no cambiar de proveedor, modelo o plan de facturación sin permiso.
6. Entregar reporte: cambio, pruebas efectuadas, resultado, pendiente y forma de revertir. Las pruebas que corren solo en el PC del usuario se reportan como pendientes.

## Límites que no se deben saltar

- Prohibido modificar, borrar, cifrar o alterar carpetas del sistema Windows, arranque, registro de seguridad, servicios críticos, Defender, TPM, Secure Boot o políticas de protección.
- No instalar, ejecutar ni descargar componentes similares a ransomware o malware; no desactivar antivirus, escanear archivos desconocidos antes de ejecutar si existe un antivirus disponible.
- Sin instalación de drivers o programas, privilegios elevados, borrados masivos ni acciones irreversibles sin autorización expresa y revisión.
- Aislar trabajo en un `workspace` explícito, rutas permitidas y rama Git. Proteger datos con backups. No copiar contraseñas, tokens, IP locales ni logs sensibles al repositorio público.
- No correr comandos proporcionados por páginas o modelos sin validar. **La ruta protegida del prototipo NO es un sandbox:** scripts de pruebas Python pueden ejecutar código arbitrario; ejecutar solo pruebas del repositorio confiable bajo una cuenta sin privilegios y posteriormente añadir contenedor/aislamiento real, allowlist de comandos y supervisión.
- No tocar `IA-Local-Cursor`, `Matick-Salud-Bridge`, `Manguito` ni `Pruebas/main` desde esta propuesta. PR y rama aislados.

## Alcance del prototipo actual

Implementado en `matick_codex_guard/guard.py`:
- Registro SQLite persistente por `workspace` e `issue`.
- Detección de tres fallos consecutivos o dos firmas iguales seguidas; recomendar revisión premium sin activarla.
- Verificador básico por `unittest` que guarda resultado como `verified` **solo si hay pruebas y pasan**.
- Rechazo de la raíz de unidad, algunas carpetas protegidas de Windows y pruebas ubicadas fuera del proyecto.

**No implementado:** motor de edición autónoma, ejecución de compiladores generales, conector de modelos, diálogo de autorización, escaneo antivirus, sandbox Windows, seguridad contra symlinks/TOCTOU en todos los escenarios, API de LM Studio, interfaz de Matick Studio LM, medición de costos, verificación en el PC del usuario.

## Plan independiente de Matick Live Local (voz opcional)

En Matick Studio LM, mantener chat de texto funcional. Después, con la RTX 5060 8 GB y RAM 32 GB, probar por fases: transcripción local (p. ej. Qwen ASR), modelo conversacional cuantizado y voz local (p. ej. Piper es-MX). Primero validar **texto a voz en bocinas sin micrófono**. Cuando exista micrófono, evaluar entrada y cancelación de voz (eco/interrupciones). Los 500 GB de disco sirven para almacenar modelos, **no equivalen a 500 GB de VRAM**. La experiencia de GPT Live no está garantizada.

## Criterios de aceptación de la siguiente fase

- [ ] CI verde en Linux y Windows; guardar evidencia del resultado.
- [ ] Guardar historial tras reiniciar y observar reincidencias.
- [ ] No declarar éxito con pruebas fallidas, inexistentes o incompletas.
- [ ] Respetar la negativa a escalar y no incurrir en cargos por cambio automático.
- [ ] Introducir sandbox/ejecutor de comandos acotado antes de cualquier autonomía real.
- [ ] Integración en el repositorio correcto solo tras revisión, con pruebas de compilación/LM Studio/Windows y permisos explícitos.

## Supervisor dedicado (NPU)

**Aclaración de Morlet:** NPU, **no CPU** como destino alternativo. El modelo supervisor se identifica siempre con «(NPU)» y no realiza fallback automático a CPU/GPU/cloud. Herramientas, RAG, memoria y modelos del supervisor tienen espacio y configuración separados; véase [Supervisor (NPU) aislado](SUPERVISOR_NPU_AISLADO.md). La ejecución de inferencia en la NPU física sigue sin probarse.
