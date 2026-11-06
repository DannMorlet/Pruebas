# Mapa de repositorios Morlet · Organización y limpieza 2026-11-06

> Índice maestro de trabajo para ChatGPT, Codex, Claude y otros agentes. Contiene **separación de responsabilidades y rutas para PR**, no una fusión de los cuatro proyectos. Auditado con GitHub el 6 de noviembre de 2026; los conteos cambian con cada push/merge.

## Cada proyecto tiene su lugar

| Repositorio | Producto / responsabilidad | Pull requests abiertos* | Ramas observadas* | Detalle |
|---|---|---:|---:|---|
| [IA-Local-Cursor](https://github.com/DannMorlet/IA-Local-Cursor) | **Matick Studio LM Cloud/Windows**: UI DirectX 12, backend independiente, inferencia, Matick Codex | 20 | 65 | [Orden](https://github.com/DannMorlet/IA-Local-Cursor/blob/main/docs/ORDEN_Y_LIMPIEZA_2026-11-06.md) |
| [Matick-Salud-Bridge](https://github.com/DannMorlet/Matick-Salud-Bridge) | **Matick Reloj**: Android POCO F6, Health Connect, Galaxy Fit3, Clare y cliente Unsloth | 12 | 16 | [Orden](https://github.com/DannMorlet/Matick-Salud-Bridge/blob/main/docs/ORDEN_Y_LIMPIEZA_2026-11-06.md) |
| [Manguito](https://github.com/DannMorlet/Manguito) | **Manguito.exe**: entrenar/destilar/podar/fusionar/cuantizar/optimizador | 5 | 8 | [Orden](https://github.com/DannMorlet/Manguito/blob/main/docs/ORDEN_Y_LIMPIEZA_2026-11-06.md) |
| [Pruebas](https://github.com/DannMorlet/Pruebas) | Laboratorio separado: prototipos Gaming, AoE2, Conquista, Fresita y **futuro SDK Muse** | 4 | 5 | Este índice |

*Foto de la auditoría: **41 PR** abiertos y **94 ramas** entre los cuatro repositorios. La captura de actividad con 58 PR representa otro momento/conjunto, no prueba de 58 abiertos actuales.

## Orden de trabajo en Pruebas
- `main/prototype/`: vista previa Gaming/Matick; no es el producto Matick Studio LM Cloud.
- [PR #2](https://github.com/DannMorlet/Pruebas/pull/2): documentos del puente AoE2 DE ↔ LM Studio.
- [PR #3](https://github.com/DannMorlet/Pruebas/pull/3): arquitectura AoE2 con 7 IAs.
- [PR #4](https://github.com/DannMorlet/Pruebas/pull/4): Conquista Family Lite, aislado en `experiments/`.
- [PR #5](https://github.com/DannMorlet/Pruebas/pull/5): Fresita Studio, Windows x64, **no confundir con Manguito.exe**.
- Los cuatro PR anteriores están sobre `main` y requieren revisión independiente; no borrarlos ni fusionarlos automáticamente.

## SDK oficial Muse: destino futuro
- Repositorio de origen: https://github.com/facebookincubator/muse-gadget-sdk
- Licencia registrada por GitHub: **Apache-2.0**; >1,300 entradas en árbol (`esp32/`, `linux/`, `android/`, `ios/`, `protocols/`, `skills/`, etc.).
- **Todavía NO se ha copiado** el SDK a `Pruebas` en esta limpieza. Destino propuesto: `third_party/muse-gadget-sdk/`, preservando `LICENSE`, versión, commit origen y cambios locales, preferentemente como submódulo cuando se confirme forma de distribución.
- Antes de incorporar archivos revisar claves/firmas/ejemplos distribuidos por upstream y atribuciones. No ejecutar scripts desconocidos ni copiar secretos. Tener el SDK de Meta **no hace que Galaxy Fit3 sea Muse Charm** ni expone automáticamente un protocolo compatible de Samsung.
- Probar SDK de Muse en una rama de integración propia y medir compatibilidad, sin mezclarlo con firmware/Watch.
- SDK pendiente como tarea independiente para no sobreescribir `Pruebas/main`.

## Políticas de orden y limpieza
1. Cada cambio va al repo del **producto propietario**, no a la carpeta de otro producto: Matick Studio LM ≠ LM Studio ≠ Manguito ≠ Unsloth Studio ≠ Matick Reloj ≠ Fresita.
2. PR apilados se revisan según sus `base`; un PR puede ser parte de otro. **No fusionar por fecha o versión**.
3. Etiquetas existentes `bug`, `enhancement`, `documentation` aplicadas a los 41 PR abiertos para facilitar filtros. Conservar el estado `draft` donde exista.
4. Antes de cerrar un PR/retirar una rama: comparar el diff, validar tests, verificar la rama receptora y pedir autorización. No cerrar ni borrar nada en masa.
5. No subir `venv/`, `node_modules/`, `dist/`, pesos GGUF, secretos, binarios privados o APK temporales a los repositorios de código.
6. Para descargas de APK/EXE verificadas usar GitHub Actions o **Releases** con hashes y firma; no confundir la existencia del código con éxito de pruebas en el dispositivo.
7. Los cuatro `main` se observaron **sin protección de rama**. Considerar reglas de aprobación, chequeos CI y deshabilitar auto-merge para cambios sensibles desde Settings, sin ejecutarlo desde este índice.
8. No tocar el firmware de Galaxy Fit3 ni el entorno local de Windows durante una limpieza documental.

## Estado de esta intervención
**Hecho:** auditoría, etiquetas y documentación de la organización. **No hecho:** borrado de archivos/ramas, cierre de PR, merge de stacks, consolidación automática de código, importación física del SDK Muse ni cambios en dispositivos. Esas operaciones necesitarán sus propias pruebas y autorización cuando puedan afectar funciones.
