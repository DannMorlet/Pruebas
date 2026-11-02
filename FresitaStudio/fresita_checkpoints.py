"""Opciones conservadoras de checkpoints LoRA/QLoRA sin importar PyTorch."""
from __future__ import annotations


def checkpoint_settings(steps, interval=0):
    """Genera opciones TRL: 0 desactiva; >0 guarda como máximo 2 checkpoints.

    No reanuda trabajos ni modifica pesos originales. El Trainer guarda el
    estado de optimizador por defecto para una futura reanudación verificada.
    """
    if type(steps) is not int or not 1 <= steps <= 10000:
        raise ValueError("Pasos de entrenamiento fuera de rango (1-10000).")
    if type(interval) is not int or not 0 <= interval <= steps:
        raise ValueError("El intervalo de checkpoints debe ser entero entre 0 y pasos.")
    if interval == 0:
        return {"save_strategy": "no"}
    return {
        "save_strategy": "steps",
        "save_steps": interval,
        "save_total_limit": 2,
        "save_only_model": False,
    }
