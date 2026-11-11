# Matick Codex Guard — prototipo independiente

El módulo es **experimental**, no reemplaza Matick Studio LM ni controla el sistema de Windows.

Requiere Python >=3.10 (sin dependencias externas). Crear/usar un proyecto propio con carpeta `tests` y archivos `test*.py`. Este comando **ejecuta código de esas pruebas**, por lo que solo debe usarse en repositorios confiables y, antes de automatizar, con sandbox de bajo privilegio.

```powershell
python -m matick_codex_guard.guard failure --workspace "C:\ruta\a\mi-proyecto" --issue "build-01" --error "falló compilación"
python -m matick_codex_guard.guard status --workspace "C:\ruta\a\mi-proyecto" --issue "build-01"
python -m matick_codex_guard.guard verify --workspace "C:\ruta\a\mi-proyecto" --issue "build-01" --tests-dir tests
python -m unittest discover -s matick_codex_guard/tests -v
```

Se debe ejecutar desde la raíz de este repositorio o con este módulo en el `PYTHONPATH`.

El historial se guarda en `~/.matick_codex_guard/history.sqlite3` (fuera del repositorio público). La herramienta **no borra ni cambia código**, no instala dependencias, no se conecta a LLM ni compra créditos. La salida incluye `recommend_astra` como **recomendación**, nunca `astra_activated=true`.

**Limitaciones conocidas:** no hay aislamiento real para scripts `unittest` ni escaneo de malware, solo prevención básica de rutas y ningún acceso automático al modelo caro. No ejecutarlo con permisos de administrador. Un valor `verified` confirma que pasó la suite seleccionada, no garantiza que toda la aplicación esté libre de errores. Consultar [acuerdos](../docs/MATICK_CODEX_AUTONOMIA_2026-11-11.md).
