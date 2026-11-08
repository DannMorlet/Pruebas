# Plan técnico Fresita Studio

## Estado actual (2026-11-01)
- [x] Espacio GitHub para Fresita en rama independiente.
- [x] Arquitectura inicial, compatibilidad objetivo y guía de desarrollo documentadas.
- [ ] Migrar totalidad del código de Fresita 0.1/0.2 al repositorio.
- [ ] Implementar CI real y verificar artefacto .exe Windows x64.
- [ ] Probar CUDA y entrenamiento LoRA en RTX 5060 física.
- [ ] Agregar diagnósticos de VRAM y estimación de memoria con margen.

## Módulos propuestos
| Área | Primera meta funcional | Estado |
|---|---|---|
| Modelos | catálogo local, metadatos safetensors | planificado |
| Creador IA | parámetros, capas, tokenizer, guardado safetensors | planificado |
| Entrenador | SFT/LoRA/QLoRA con validaciones | planificado |
| Preferencias | limpieza DPO y entrenador DPO | planificado |
| Destilación | profesor-alumno con datos auditables | investigación |
| Editor | vocabulario, capas, poda y LoRA sin sobrescribir originales | investigación |
| Multimodal | adaptadores de audio, visión y video con presupuesto real | investigación |
| Evaluación | tareas en español MX, código, matemáticas, regresiones | planificado |
| Matick | 4 estudiantes ~600M, después 1,000 especialistas | investigación |

## Advertencias de capacidad
- Reducir 4B a 600M implica arquitecturas nuevas, entrenamiento y pérdida de capacidad; 4-bit no altera el número de parámetros.
- 2.4M x 1000 = 2.4B parámetros independientes; no equivale automáticamente a un modelo denso de 2.4B.
- Los 4 profesores o estudiantes y los 1,000 miniagentes no deben duplicar innecesariamente pesos en memoria.
- Unsloth es un backend opcional: comprobar modelos soportados, licencia y compatibilidad.
- Supervisar el consumo de RAM/VRAM y no afirmar que los cuatro modelos grandes pueden entrenarse juntos en una sola 5060 de 8 GB.

## Entregables de próxima etapa
- Código Python de GUI + worker reales subidos.
- Pruebas automatizadas y guía de instalación reproducible.
- Workflow de GitHub Actions que emite .exe Windows x64 de verdad.
- Evidencia de prueba del ejecutable en Windows; distinguir CI de pruebas en la GPU física.
