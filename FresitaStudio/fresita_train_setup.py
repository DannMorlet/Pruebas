"""Instalación guiada y aislada de dependencias LoRA/QLoRA en Windows x64.

No instala nada al importar. Sólo crea un .venv nuevo tras confirmación
explícita en la GUI; nunca actualiza entornos existentes ni controladores.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

from fresita_core import BASE

TORCH_VERSION = "2.14.1"
TORCH_INDEX = "https://download.pytorch.org/whl/cu132"
STAGE_TIMEOUT_S = 2400

class SetupCancelled(RuntimeError):
    pass

def build_setup_plan(qlora=False, *, workspace=None, bundle_root=None):
    """Plan determinista. No ejecuta procesos ni toca archivos."""
    if type(qlora) is not bool:
        raise ValueError("QLoRA debe ser verdadero o falso")
    root = Path(workspace) if workspace is not None else BASE
    bundle = (Path(bundle_root) if bundle_root is not None else
              Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)))
    req = bundle / "requirements-train.txt"
    if not req.is_file():
        raise FileNotFoundError("Falta requirements-train.txt dentro de Fresita.")
    venv = root / ".venv"
    if venv.exists() or venv.is_symlink():
        raise FileExistsError(
            "Ya existe el entorno .venv. No se reemplazará ni actualizará. "
            "Usa el diagnóstico o realiza una migración manual con respaldo.")
    python = venv / "Scripts" / "python.exe"
    pip = [str(python), "-m", "pip", "--isolated", "install",
           "--disable-pip-version-check", "--no-input", "--only-binary=:all:"]
    commands = [
        ("Comprobar Python 3.12 x64", [
            "py", "-3.12", "-c",
            "import sys,struct; assert sys.version_info[:2]==(3,12) and struct.calcsize('P')==8"
        ]),
        ("Crear entorno aislado", ["py", "-3.12", "-m", "venv", str(venv)]),
        ("Instalar PyTorch CUDA 13.2", pip + [
            f"torch=={TORCH_VERSION}", "--index-url", TORCH_INDEX
        ]),
        ("Instalar TRL, PEFT y dependencias", pip + ["-r", str(req)]),
    ]
    if qlora:
        commands.append(("Instalar bitsandbytes para QLoRA", pip + ["bitsandbytes"]))
    return {"venv": venv, "python": python, "qlora": qlora,
            "commands": commands, "requirements": req}

def _terminate_tree(proc):
    """Termina sólo el proceso creado por Fresita y sus hijos."""
    if proc.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=15, check=False)
        except (OSError, subprocess.TimeoutExpired):
            proc.terminate()
    else:
        proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)

def _run_command(command, cancel):
    if cancel.is_set():
        raise SetupCancelled("Instalación cancelada antes de iniciar otra etapa.")
    env = os.environ.copy()
    # El entorno de usuario no debe cambiar el índice o inyectar rutas Python.
    for name in list(env):
        if name.upper().startswith("PIP_") or name.upper() in ("PYTHONPATH", "PYTHONHOME"):
            env.pop(name, None)
    flags = (getattr(subprocess, "CREATE_NO_WINDOW", 0) |
             getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    proc = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            env=env, creationflags=flags, shell=False)
    started = time.monotonic()
    try:
        while True:
            if cancel.is_set():
                raise SetupCancelled("Instalación cancelada por el usuario.")
            if time.monotonic() - started > STAGE_TIMEOUT_S:
                raise TimeoutError("Una etapa de instalación excedió el tiempo permitido.")
            try:
                return proc.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                pass
    finally:
        if proc.poll() is None:
            _terminate_tree(proc)

def run_setup(plan, *, on_stage=None, cancel=None, runner=None, platform=None):
    """Ejecuta el plan sólo en Windows. Rechaza entornos previos y revierte fallos.

    runner(command, cancel) permite pruebas sin red, pip o CUDA.
    """
    if (platform if platform is not None else os.name) != "nt":
        raise OSError("La instalación guiada está disponible sólo en Windows x64.")
    if cancel is None:
        cancel = threading.Event()
    if cancel.is_set():
        raise SetupCancelled("Instalación cancelada antes de comenzar.")
    venv = Path(plan["venv"])
    if venv.exists() or venv.is_symlink():
        raise FileExistsError("El entorno .venv ya existe; no se modificó.")
    run = runner if runner is not None else _run_command
    marker = venv / ".fresita-setup-in-progress"
    created = False
    try:
        for index, (stage, command) in enumerate(plan["commands"]):
            if cancel.is_set():
                raise SetupCancelled("Instalación cancelada.")
            if on_stage:
                on_stage(stage)
            if index == 1:
                venv.mkdir(parents=True, exist_ok=False)
                created = True
                marker.write_text("Creado por el instalador de Fresita.\n", encoding="utf-8")
            code = run(command, cancel)
            if code != 0:
                raise RuntimeError(
                    "No se completó: " + stage +
                    ". Comprueba Python, espacio disponible, conexión y compatibilidad.")
            if index == 1 and not Path(plan["python"]).is_file():
                raise RuntimeError("El entorno creado no contiene Python x64.")
        if not Path(plan["python"]).is_file():
            raise RuntimeError("No se encontró Python al finalizar la instalación.")
        marker.unlink()
        return {"ok": True, "qlora": plan["qlora"]}
    except Exception:
        # Sólo se borra el directorio que esta ejecución creó y marcó.
        if created and marker.is_file() and not venv.is_symlink():
            try:
                shutil.rmtree(venv)
            except OSError:
                # Si Windows bloquea un archivo, queda la marca para revisión.
                pass
        raise
