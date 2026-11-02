"""Instalación optativa de Unsloth Core en venv independiente para Windows x64.

El instalador requiere Python 3.13 y uv ya instalados. No ejecuta comandos
al importar; conserva .venv (TRL/PEFT) y nunca actualiza controladores.
La instalación exitosa no equivale a entrenamiento CUDA verificado.
"""
from __future__ import annotations

from pathlib import Path
import sys

from fresita_core import BASE
from fresita_train_setup import run_setup, SetupCancelled

ENV_NAME = ".venv-unsloth"
POST_INSTALL_CHECK = """
import importlib.metadata as m
import struct
import sys
import torch

if sys.version_info[:2] != (3, 13) or struct.calcsize('P') != 8:
    raise RuntimeError('Se requiere Python 3.13 x64')
if not torch.version.cuda:
    raise RuntimeError('PyTorch no incluye CUDA NVIDIA')
for name in ('torchao', 'unsloth', 'unsloth_zoo', 'trl', 'peft'):
    m.version(name)
print('Paquetes de Unsloth instalados y wheel CUDA presente; GPU no validada')
"""

def build_unsloth_setup_plan(*, workspace=None):
    """Construye comandos uv oficiales, sin ejecutarlos ni instalar globalmente."""
    root = Path(workspace) if workspace is not None else BASE
    venv = root / ENV_NAME
    if venv.exists() or venv.is_symlink():
        raise FileExistsError(
            "Ya existe .venv-unsloth. No se sobrescribirá; conserva tu entorno.")
    python = venv / "Scripts" / "python.exe"
    commands = [
        ("Verificar Python 3.13 x64",
         ["py", "-3.13", "-c",
          "import sys,struct; assert sys.version_info[:2]==(3,13) and struct.calcsize('P')==8"]),
        ("Crear entorno Unsloth separado",
         ["uv", "venv", "--no-python-downloads", "--python", "3.13", str(venv)]),
        ("Instalar torchao primero (recomendación oficial Windows)",
         ["uv", "pip", "install", "--python", str(python), "torchao"]),
        ("Instalar Unsloth con backend PyTorch automático",
         ["uv", "pip", "install", "--python", str(python),
          "unsloth", "--torch-backend=auto"]),
        ("Comprobar dependencias del entorno Unsloth",
         ["uv", "pip", "check", "--python", str(python)]),
        ("Comprobar versiones y compilación CUDA",
         [str(python), "-I", "-c", POST_INSTALL_CHECK]),
    ]
    return {"venv":venv,"python":python,"qlora":False,
            "commands":commands,"environment":ENV_NAME}

def run_unsloth_setup(plan, *, on_stage=None, cancel=None, runner=None, platform=None):
    """Reutiliza cancelación, no-sobrescritura y rollback de run_setup."""
    if Path(plan.get("venv", "")).name != ENV_NAME:
        raise ValueError("Sólo se permite instalar en .venv-unsloth.")
    return run_setup(plan, on_stage=on_stage, cancel=cancel,
                     runner=runner, platform=platform)
