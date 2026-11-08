"""Conquista Family Lite: prueba del formato universal (sin gráficos ni red)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath


class FamilyError(ValueError):
    """Datos, edición o versión incompatibles."""


def read_family(path: str | Path) -> dict:
    """Lee un manifiesto JSON y comprueba el identificador de formato."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FamilyError(f"No se pudo leer el manifiesto: {exc}") from exc
    if not isinstance(data, dict) or data.get("format") != "family/1":
        raise FamilyError("Se requiere un objeto JSON con format='family/1'")
    return data


def safe_asset(name: object) -> str:
    """Solo permite rutas lógicas relativas, sin traversal ni URL."""
    if not isinstance(name, str) or not name or "\\" in name or "://" in name:
        raise FamilyError("Identificador de recurso inválido")
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or "." in p.parts:
        raise FamilyError("Ruta de recurso no permitida")
    return name


def validate_edition(edition: dict) -> None:
    if edition.get("type") != "edition":
        raise FamilyError("Se requiere un manifiesto de edición")
    generations = edition.get("generations")
    if (not isinstance(generations, list) or not generations
            or not all(isinstance(g, str) and g for g in generations)
            or len(generations) != len(set(generations))):
        raise FamilyError("Lista de generaciones inválida")
    cap = edition.get("max_fps")
    if type(cap) is not int or cap < 1 or cap > 1200:
        raise FamilyError("Límite de FPS inválido")


def resolve_visual(item: dict, edition: dict, generation: str) -> dict:
    """Obtiene una representación, nunca modifica estadísticas del juego."""
    validate_edition(edition)
    if not edition.get("enabled", False):
        raise FamilyError("Esta edición aún no está habilitada")
    if generation not in edition["generations"]:
        raise FamilyError(f"La generación {generation} no pertenece a esta edición")
    if item.get("type") != "item_visual" or not isinstance(item.get("entity_id"), str):
        raise FamilyError("Manifiesto de objeto inválido")
    visuals = item.get("visuals")
    if not isinstance(visuals, dict):
        raise FamilyError("El catálogo visual no es válido")
    visual = visuals.get(generation, item.get("fallback"))
    if not isinstance(visual, dict):
        raise FamilyError("No existe un recurso ni alternativa compatible")
    model = safe_asset(visual.get("model"))
    effect = visual.get("effect")
    if not isinstance(effect, str) or not effect:
        raise FamilyError("Efecto no válido")
    return {
        "entity_id": item["entity_id"],
        "generation": generation,
        "model": model,
        "effect": effect,
        "max_fps": edition["max_fps"],
    }


def project_combat_event(event: dict, appearance: dict) -> dict:
    """Proyecta el evento del servidor; no altera daño ni tiempos."""
    if event.get("type") != "combat.hit" or not isinstance(event.get("entity_id"), str):
        raise FamilyError("Evento de combate inválido")
    if event["entity_id"] != appearance["entity_id"]:
        raise FamilyError("Objeto visual distinto al que atacó")
    if type(event.get("damage")) is not int or event["damage"] < 0:
        raise FamilyError("Daño inválido")
    return {"event": dict(event), "appearance": dict(appearance)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Prueba visual lógica Family Lite")
    parser.add_argument("--edition", required=True)
    parser.add_argument("--item", required=True)
    parser.add_argument("--generation", required=True)
    args = parser.parse_args()
    appearance = resolve_visual(
        read_family(args.item), read_family(args.edition), args.generation
    )
    print(json.dumps(appearance, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
