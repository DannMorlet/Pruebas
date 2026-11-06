#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vista previa de dos subagentes GPU para AoE2 DE (sin controlar el juego).

Un modelo local de LM Studio puede representar a Tyran y Mazapan mediante
prompts separados. No instala drivers, no carga modelos, no envía órdenes
al juego, y NO accede a mouse/teclado del usuario.
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib import error, request

AGENTS = {
    "Tyran": "Eres Tyran, analista militar metódico. Elige una sola prioridad breve.",
    "Mazapan": "Eres Mazapan, economista táctico creativo. Elige una prioridad breve.",
}
DECISIONS = {"economy", "defend", "scout", "attack", "repair", "fortify", "trade", "chat"}


def clean_state(raw: str) -> dict:
    """Solo aceptar un diccionario JSON compacto de observaciones ya filtradas."""
    if len(raw) > 10000:
        raise ValueError("El estado es demasiado largo; primero resúmelo.")
    state = json.loads(raw)
    if not isinstance(state, dict):
        raise ValueError("El estado debe ser un objeto JSON.")
    return state


def validate_proposal(text: str) -> dict:
    """Si el modelo pequeño falla, proponer defensa sin ejecutar nada."""
    try:
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Se esperaba objeto")
        decision = str(data.get("decision", "")).lower().strip()
        if decision not in DECISIONS:
            raise ValueError("Decisión fuera de lista")
        reason = str(data.get("reason", ""))[:220]
        return {"decision": decision, "reason": reason, "valid": True}
    except (ValueError, TypeError, json.JSONDecodeError):
        return {
            "decision": "defend",
            "reason": "Salida del modelo no válida. Fallback conservador.",
            "valid": False,
        }


def prompt_for(agent: str, state: dict) -> list[dict]:
    if agent not in AGENTS:
        raise ValueError("Solo existen Tyran y Mazapan como subagentes GPU.")
    instruction = (
        AGENTS[agent]
        + " Selecciona SOLO una prioridad según información visible, "
          "sin inventar recursos ni coordenadas, ni órdenes de sistema. "
          "Devuelve exclusivamente JSON: "
          '{"decision":"defend","reason":"explicación breve"}. '
        + "Decisiones permitidas: " + ", ".join(sorted(DECISIONS)) + "."
    )
    return [
        {"role": "system", "content": instruction},
        {"role": "user", "content": json.dumps(state, ensure_ascii=False, separators=(",", ":"))},
    ]


def ask_lm_studio(base: str, model: str, messages: list[dict], timeout: float) -> str:
    if not base.startswith(("http://127.0.0.1:", "http://localhost:")):
        raise ValueError("El prototipo solo permite LM Studio local en localhost.")
    url = base.rstrip("/") + "/chat/completions"
    payload = json.dumps({
        "model": model, "messages": messages, "temperature": 0.25,
        "max_tokens": 128, "stream": False,
    }).encode("utf-8")
    req = request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=timeout) as resp:
        answer = json.load(resp)
    return str(answer["choices"][0]["message"].get("content") or "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agente", required=True, choices=list(AGENTS))
    parser.add_argument("--estado", default='{"aldeanos":3,"enemigos_visibles":0,"recursos":{"comida":100}}')
    parser.add_argument("--modelo", help="ID exacto del modelo YA CARGADO en LM Studio")
    parser.add_argument("--api-base", default="http://127.0.0.1:1234/v1")
    parser.add_argument("--consultar", action="store_true", help="consulta una vez LM Studio; nunca ejecuta órdenes")
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args(argv)
    try:
        state = clean_state(args.estado)
        messages = prompt_for(args.agente, state)
        if args.consultar:
            if not args.modelo:
                raise ValueError("Indica --modelo con un ID exacto ya cargado.")
            if not 1 <= args.timeout <= 30:
                raise ValueError("El timeout debe estar entre 1 y 30 segundos.")
            output = ask_lm_studio(args.api_base, args.modelo, messages, args.timeout)
            proposal = validate_proposal(output)
            source = "lm_studio"
        else:
            proposal = {"decision": "defend", "reason": "Simulación sin inferencia", "valid": True}
            source = "simulacion"
        print(json.dumps({
            "agent": args.agente,
            "source": source,
            "proposal": proposal,
            "executed_in_game": False,
        }, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, IndexError, error.URLError, TimeoutError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
