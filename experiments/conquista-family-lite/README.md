# Conquista Family Lite · Prueba v0.1

**Estado: prototipo de datos, no cliente jugable.**

Este experimento comprueba el principio de Conquista Family: **un mismo objeto lógico se representa de forma distinta en generaciones 1.0 y 2.0**, sin cambiar sus estadísticas o eventos del servidor.

## Alcance

- Formato textual `.family.json`, versión `family/1`.
- Edición Lite habilitada para generaciones visuales **1.0 y 2.0** y un techo de **60 FPS** configurable.
- Ediciones Standard (1.0–5.0) y Ultimate (1.0–11.0) **reservadas y deshabilitadas**.
- Resolución visual de la Katana de nivel 5: básico en 1.0 y brillo ligero en 2.0.
- Rechazo de generaciones fuera de edición, manifiestos inválidos y rutas de recursos inseguras.
- Misma información de combate para dos presentaciones visuales del mismo objeto.
- Pruebas automáticas con la biblioteca estándar de Python; **sin dependencias externas**.

## Ejecutar localmente

Requiere Python 3.10+.

```bash
cd experiments/conquista-family-lite
python -m unittest discover -s tests -v
python family_lite.py --edition data/editions/lite.family.json --item data/items/katana.level5.family.json --generation 1.0
python family_lite.py --edition data/editions/lite.family.json --item data/items/katana.level5.family.json --generation 2.0
```

La salida es JSON y muestra dos representaciones del **mismo ID universal**.

## Importante

Los nombres de recursos (p. ej. `concept/katana_classic`) son **etiquetas de prueba**, no referencias a archivos originales, ni modelos 3D. No incluye ejecutables, imágenes, protocolos ni archivos de TQ. No existe servidor multijugador, renderizador, detección de hardware, física completa ni un FPS real medido. La compatibilidad futura requerirá adaptadores y recursos legalmente utilizables.

## Siguiente objetivo

Construir un pequeño cliente 2D propio que lea los manifiestos e intercambie las variantes 1.0/2.0 sin perder estado, seguido de un servidor autoritativo compartido.
