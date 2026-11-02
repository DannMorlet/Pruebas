"""Preferencias locales y avisos de actualización del motor llama.cpp.

Sin red, sin descargas ni ejecución de procesos al importar.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile

from fresita_core import BASE

DEFAULT_AUTOCHECK = True

def settings_path(root=None):
    return Path(root or BASE) / "config" / "actualizaciones.json"

def load_settings(root=None):
    """Ante archivo ausente o corrupto, usa valores seguros; nunca instala nada."""
    path = settings_path(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and type(data.get("buscar_al_abrir")) is bool:
            return {"buscar_al_abrir": data["buscar_al_abrir"]}
    except (OSError, ValueError, TypeError):
        pass
    return {"buscar_al_abrir": DEFAULT_AUTOCHECK}

def save_settings(autocheck, root=None):
    if type(autocheck) is not bool:
        raise ValueError("La preferencia debe ser verdadero o falso")
    path = settings_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=".actualizaciones-", suffix=".tmp", delete=False
        ) as f:
            tmp = Path(f.name)
            json.dump({"buscar_al_abrir": autocheck}, f, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    return path

def update_message(installed, available):
    """No confunde builds bNNNN con releases estables; compara sólo builds."""
    if not re.fullmatch(r"b[0-9]+", str(available)):
        raise ValueError("Versión disponible inválida")
    if installed is None:
        return f"Motor no instalado · Disponible {available}"
    if not re.fullmatch(r"b[0-9]+", str(installed)):
        raise ValueError("Versión instalada inválida")
    current, latest = int(installed[1:]), int(available[1:])
    if current < latest:
        return f"Actualización disponible: {installed} → {available}"
    if current == latest:
        return f"Motor al día: {installed}"
    return f"Versión local {installed} más reciente que la consultada ({available})"
