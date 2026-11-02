"""Reanudación explícita y conservadora de checkpoints TRL, sin importar CUDA."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re

from fresita_checkpoints import checkpoint_settings

_MANIFEST = "fresita_checkpoint_manifest.json"
_FIELDS = ("model", "qlora", "rank", "steps", "lr", "checkpoint_interval")
_REQUIRED = ("trainer_state.json", "optimizer.pt", "scheduler.pt", "rng_state.pth")


def _file_sha256(path):
    source = Path(path).expanduser().resolve(strict=True)
    if not source.is_file():
        raise ValueError("El dataset de la receta debe ser un archivo.")
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def recipe_fingerprint(cfg):
    """Huella sin rutas, ejemplos ni identificadores de modelos en el manifiesto."""
    if not isinstance(cfg, dict):
        raise ValueError("La receta debe ser un objeto JSON.")
    try:
        data = {key: cfg[key] for key in _FIELDS}
        data["dataset_sha256"] = _file_sha256(cfg["dataset"])
        data["eval_sha256"] = (_file_sha256(cfg["eval_dataset"])
                               if cfg.get("eval_dataset") else None)
    except KeyError as exc:
        raise ValueError("Falta un campo necesario para reanudar.") from exc
    encoded = json.dumps(data, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def prepare_training_run(cfg):
    """Prepara guardado nuevo o valida reanudación; devuelve ruta o None.

    Nunca selecciona automáticamente el checkpoint más reciente. Una reanudación
    requiere receta idéntica, datasets sin cambios y estado de Trainer completo.
    """
    steps = cfg.get("steps")
    interval = cfg.get("checkpoint_interval", 0)
    checkpoint_settings(steps, interval)
    requested = cfg.get("resume_checkpoint")
    if not interval:
        if requested:
            raise ValueError("Activa checkpoints antes de solicitar reanudación.")
        return None

    output = Path(cfg["output"]).expanduser().resolve()
    manifest = output / _MANIFEST
    fingerprint = recipe_fingerprint(cfg)

    if not requested:
        if output.exists() and any(output.iterdir()):
            raise ValueError("La carpeta de salida ya contiene archivos; no se sobrescribe.")
        output.mkdir(parents=True, exist_ok=True)
        temp = output / (_MANIFEST + ".tmp")
        try:
            with temp.open("x", encoding="utf-8") as handle:
                json.dump({"version": 1, "fingerprint": fingerprint}, handle)
            os.replace(temp, manifest)
        finally:
            temp.unlink(missing_ok=True)
        return None

    if not manifest.is_file() or manifest.stat().st_size > 4096:
        raise ValueError("Falta un manifiesto válido de Fresita para reanudar.")
    try:
        stored = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("El manifiesto de checkpoint está dañado.") from exc
    if (not isinstance(stored, dict) or stored.get("version") != 1
            or stored.get("fingerprint") != fingerprint):
        raise ValueError("La receta o los datasets no coinciden con el checkpoint.")

    selected = Path(requested).expanduser()
    if selected.is_symlink():
        raise ValueError("No se admiten enlaces simbólicos como checkpoint.")
    checkpoint = selected.resolve(strict=True)
    if checkpoint.parent != output or not checkpoint.is_dir():
        raise ValueError("El checkpoint debe estar dentro de la salida del experimento.")
    match = re.fullmatch(r"checkpoint-([1-9][0-9]*)", checkpoint.name)
    if not match:
        raise ValueError("El nombre del checkpoint no es válido.")
    step = int(match.group(1))
    if step > steps:
        raise ValueError("El checkpoint supera los pasos de la receta.")
    for filename in _REQUIRED:
        file = checkpoint / filename
        if not file.is_file() or file.stat().st_size == 0:
            raise ValueError("Checkpoint incompleto: falta estado del entrenador.")
    state_file = checkpoint / "trainer_state.json"
    if state_file.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("Estado de entrenador demasiado grande.")
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("Estado del entrenador ilegible.") from exc
    if not isinstance(state, dict) or type(state.get("global_step")) is not int or state["global_step"] != step:
        raise ValueError("Los pasos del checkpoint y su estado no coinciden.")
    return checkpoint
