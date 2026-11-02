"""Reanudación explícita y conservadora de checkpoints TRL, sin importar CUDA."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import sys

from fresita_checkpoints import checkpoint_settings

_MANIFEST = "fresita_checkpoint_manifest.json"
_FIELDS = ("model", "qlora", "rank", "steps", "lr", "checkpoint_interval")
_REQUIRED = ("trainer_state.json", "optimizer.pt", "scheduler.pt", "rng_state.pth",
             "adapter_config.json", "adapter_model.safetensors")
_RUNTIME_PACKAGES = ("torch", "transformers", "trl", "peft", "accelerate",
                     "datasets", "safetensors", "tokenizers")


def installed_runtime_versions(qlora=False, *, cuda_build=None):
    """Metadatos locales, sin importar modelos, leer datasets ni usar la red.

    El wheel CUDA se pasa desde torch ya importado por el worker.
    """
    if type(qlora) is not bool:
        raise ValueError("El modo QLoRA debe ser booleano.")
    names = _RUNTIME_PACKAGES + (("bitsandbytes",) if qlora else ())
    versions = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as exc:
            raise ValueError("Falta una dependencia para guardar checkpoints: " + name) from exc
    versions["python"] = ".".join(map(str, sys.version_info[:3]))
    versions["cuda_build"] = cuda_build or "N/D"
    return versions


def runtime_fingerprint(versions):
    """Huella estable del stack de entrenamiento, sin rutas ni datasets."""
    if (not isinstance(versions, dict) or not versions or len(versions) > 24
            or any(not isinstance(k, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,39}", k)
                   or not isinstance(v, str) or not 0 < len(v) <= 80
                   or any(ord(c) < 32 for c in v)
                   for k, v in versions.items())):
        raise ValueError("Versiones de dependencias inválidas.")
    payload = json.dumps(versions, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()



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


def prepare_training_run(cfg, *, runtime_versions=None):
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
    runtime_hash = (runtime_fingerprint(runtime_versions)
                    if runtime_versions is not None else None)

    if not requested:
        if output.exists() and any(output.iterdir()):
            raise ValueError("La carpeta de salida ya contiene archivos; no se sobrescribe.")
        output.mkdir(parents=True, exist_ok=True)
        temp = output / (_MANIFEST + ".tmp")
        try:
            with temp.open("x", encoding="utf-8") as handle:
                if runtime_hash is not None:
                    json.dump({"version": 2, "fingerprint": fingerprint,
                               "runtime_sha256": runtime_hash}, handle)
                else:
                    # Sólo para compatibilidad de llamadas antiguas y pruebas.
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
    if (not isinstance(stored, dict) or type(stored.get("version")) is not int
            or stored["version"] not in (1, 2)
            or stored.get("fingerprint") != fingerprint):
        raise ValueError("La receta o los datasets no coinciden con el checkpoint.")
    if stored["version"] == 2:
        if runtime_hash is None or stored.get("runtime_sha256") != runtime_hash:
            raise ValueError(
                "Las versiones de Python, CUDA o dependencias cambiaron. "
                "No se reanudará este checkpoint con un entorno diferente.")
    # Versión 1: legado sin verificación de versiones. No inventar garantías.

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
        if file.is_symlink():
            raise ValueError("Checkpoint no confiable: contiene enlaces simbólicos.")
        if not file.is_file() or file.stat().st_size == 0:
            raise ValueError("Checkpoint incompleto: falta estado o adaptador LoRA.")
    adapter_file = checkpoint / "adapter_config.json"
    if adapter_file.stat().st_size > 64 * 1024:
        raise ValueError("Configuración del adaptador demasiado grande.")
    try:
        adapter = json.loads(adapter_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValueError("Configuración del adaptador ilegible.") from exc
    if (not isinstance(adapter, dict) or adapter.get("peft_type") != "LORA"
            or type(adapter.get("r")) is not int or adapter["r"] != cfg["rank"]):
        raise ValueError("El adaptador LoRA no coincide con el rango de la receta.")
    if (checkpoint / "adapter_model.safetensors").stat().st_size < 16:
        raise ValueError("Pesos del adaptador vacíos o truncados.")
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
