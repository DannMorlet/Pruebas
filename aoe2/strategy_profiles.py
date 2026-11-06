#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Planificador TÁCTICO DE PRUEBA para Nutella, Gemini y Copilot (#5, #6, #7).

Solo sugiere prioridades según observaciones locales ya autorizadas.
NO accede al juego, LM Studio, teclado, mouse ni archivos externos.
NO entrena ningún modelo y NO crea unidades ni recursos mágicamente.
"""
from __future__ import annotations

import argparse
import json
from typing import Any

AGENTS = ("Nutella", "Gemini", "Copilot")
AGES = ("dark", "feudal", "castle", "imperial")
GEMINI_ECONOMY = {
    "dark": {"food": 55, "wood": 35, "gold": 10, "stone": 0},
    "feudal": {"food": 45, "wood": 40, "gold": 15, "stone": 0},
    "castle": {"food": 40, "wood": 35, "gold": 20, "stone": 5},
    "imperial": {"food": 35, "wood": 35, "gold": 20, "stone": 10},
}
# Vulnerabilidades SOLO cuando el observador verificó que están a la vista.
VISIBLE_WEAKNESSES = {
    "exposed_gold", "isolated_villagers", "undefended_trade", "exposed_relic"
}


def _integer(value: Any, default: int = 0) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _yes(value: Any) -> bool:
    return value is True  # sin coerción de textos o números dudosos


def propose(agent: str, observation: dict[str, Any]) -> dict[str, Any]:
    """Devuelve una sugerencia simbólica: jamás órdenes para el motor del juego."""
    if agent not in AGENTS:
        raise ValueError("Solo Nutella, Gemini y Copilot.")
    if not isinstance(observation, dict):
        raise TypeError("Se esperaba una observación JSON de tipo objeto.")
    age = str(observation.get("age", "dark")).lower()
    if age not in AGES:
        age = "dark"  # estado ausente: recomendación conservadora
    villagers = _integer(observation.get("villagers", 3), default=3)
    idle = _integer(observation.get("idle_villagers"))
    pressure = _integer(observation.get("enemy_pressure"))
    army = _integer(observation.get("own_army"))
    houses_remaining = _integer(observation.get("housing_margin", 3))
    sight = _integer(observation.get("explored_percent"))
    food = _integer(observation.get("food"))
    wood = _integer(observation.get("wood"))
    gold = _integer(observation.get("gold"))
    hp = _integer(observation.get("army_hp_percent", 100), default=100)
    has_town_center = _yes(observation.get("town_center_exists", True))
    can_age_up = _yes(observation.get("can_advance_age"))
    have_reliable_targets = _yes(observation.get("targets_visible"))
    vuln_raw = observation.get("enemy_vulnerabilities", [])
    if not isinstance(vuln_raw, list):
        vuln_raw = []
    weak = VISIBLE_WEAKNESSES & {x for x in vuln_raw if isinstance(x, str)}
    is_ally_support_possible = _yes(observation.get("ally_ready"))
    result = {
        "agent": agent,
        "age": age,
        "action": "economy",
        "reason": "Mantener economía y producción antes de tomar riesgos.",
        "implemented_in_game": False,
        "uses_hidden_information": False,
        "uses_cheats": False,
    }
    if agent == "Gemini":
        result["economic_targets_percent"] = GEMINI_ECONOMY[age].copy()

    def set_action(name: str, why: str) -> dict[str, Any]:
        result["action"], result["reason"] = name, why
        return result

    # Invariantes compartidas: nunca abandonan la última posibilidad de producir.
    if villagers <= 1:
        return set_action("recover", "Proteger el último aldeano y reconstruir economía si es viable.")
    if not has_town_center and wood >= 275:
        return set_action("recover", "No hay centro urbano: priorizar reconstrucción con recursos reales.")
    if pressure >= 3:
        return set_action("defend", "Amenaza grave detectada: salvar aldeanos y proteger la base.")
    if houses_remaining <= 1 and wood >= 25:
        return set_action("housing", "La población está cerca del límite: construir vivienda si se puede.")

    if agent == "Nutella":
        if weak and have_reliable_targets and army >= 3 and pressure == 0:
            return set_action("harass", "Hostigar solo una vulnerabilidad enemiga observada y retirarse.")
        if pressure >= 1:
            return set_action("defend", "Resistir, dispersar riesgos y preparar la siguiente base.")
        if idle >= 1:
            return set_action("economy", "Reasignar aldeanos ociosos; expandir con discreción.")
        if wood >= 175 and villagers >= 8:
            return set_action("expand", "Asegurar recursos secundarios y crear redundancia de bases.")
        return set_action("scout", "Buscar rutas de expansión y puntos económicos sin explorar a ciegas.")

    if agent == "Gemini":
        if pressure >= 1 and hp <= 30:
            return set_action("retreat", "Retirada táctica al 30 % de vida: proteger el ejército.")
        if idle >= 1:
            return set_action("economy", "Tesorero: equilibrar aldeanos conforme al objetivo por edad.")
        if sight < 30 and pressure == 0:
            return set_action("scout", "Explorador: localizar rutas y recursos evitando torres.")
        if can_age_up and pressure == 0:
            return set_action("age_up", "Tesorero: transición de edad con recursos asegurados.")
        if is_ally_support_possible and have_reliable_targets and army >= 7:
            return set_action("flank", "Coordinación: apoyar un flanco aliado contra objetivos visibles.")
        return set_action("economy", "Optimizar producción y preparar el siguiente pico de poder.")

    # Copilot prioriza una política adaptable basada solo en datos recibidos.
    if pressure >= 1 and army < 5:
        return set_action("defend", "Defensor: amenaza visible con ejército reducido.")
    if idle >= 1 or food < 60:
        return set_action("economy", "Economista: corregir trabajo o producción deficiente.")
    if can_age_up and pressure == 0:
        return set_action("age_up", "Tecnología: transición estratégica disponible.")
    if sight < 45 and pressure == 0:
        return set_action("scout", "Explorador: reunir información antes de comprometer el ejército.")
    if have_reliable_targets and army >= 10 and pressure == 0:
        return set_action("attack", "General: atacar un objetivo visible con fuerza disponible.")
    if wood >= 220 and gold >= 100:
        return set_action("fortify", "Ingeniero: reforzar acceso y protección de recursos.")
    return set_action("economy", "Predictivo: consolidar antes de asumir más riesgo.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agente", required=True, choices=AGENTS)
    parser.add_argument("--estado", default='{"age":"feudal","villagers":12,"idle_villagers":1}')
    args = parser.parse_args()
    state = json.loads(args.estado)
    if not isinstance(state, dict):
        parser.error("El estado debe ser un objeto JSON.")
    if len(args.estado) > 15000:
        parser.error("Estado demasiado grande.")
    print(json.dumps(propose(args.agente, state), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
