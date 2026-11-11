# Matick Codex Guard — prototipo independiente

El módulo es **experimental**, no reemplaza Matick Studio LM ni controla el sistema de Windows.

Requiere Python >=3.10 (sin dependencias externas). **CI:** se verifica la compatibilidad de Python 3.11 y Python 3.15, en Linux y Windows, con matriz automática de GitHub Actions. La rama 3.15 instala la última versión de mantenimiento disponible (3.15.2 a 2026-11-11). Las pruebas reales en la PC de Morlet siguen pendientes. Crear/usar un proyecto propio con carpeta `tests` y archivos `test*.py`. Este comando **ejecuta código de esas pruebas**, por lo que solo debe usarse en repositorios confiables y, antes de automatizar, con sandbox de bajo privilegio.

```powershell
py -3.15 -m matick_codex_guard.guard failure --workspace "C:\ruta\a\mi-proyecto" --issue "build-01" --error "falló compilación"
py -3.15 -m matick_codex_guard.guard status --workspace "C:\ruta\a\mi-proyecto" --issue "build-01"
py -3.15 -m matick_codex_guard.guard verify --workspace "C:\ruta\a\mi-proyecto" --issue "build-01" --tests-dir tests
py -3.15 -m unittest discover -s matick_codex_guard/tests -v
```

Se debe ejecutar desde la raíz de este repositorio o con este módulo en el `PYTHONPATH`.

El historial se guarda en `~/.matick_codex_guard/history.sqlite3` (fuera del repositorio público). La herramienta **no borra ni cambia código**, no instala dependencias, no se conecta a LLM ni compra créditos. La salida incluye `recommend_astra` como **recomendación**, nunca `astra_activated=true`.

**Limitaciones conocidas:** no hay aislamiento real para scripts `unittest` ni escaneo de malware, solo prevención básica de rutas y ningún acceso automático al modelo caro. No ejecutarlo con permisos de administrador. Un valor `verified` confirma que pasó la suite seleccionada, no garantiza que toda la aplicación esté libre de errores. Consultar [acuerdos](../docs/MATICK_CODEX_AUTONOMIA_2026-11-11.md).
