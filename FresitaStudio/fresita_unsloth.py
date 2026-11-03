"""Diagnóstico opcional de Unsloth, sin instalación ni importación de Unsloth.

El worker se ejecuta en el .venv de entrenamiento con Python aislado.
Unsloth instalado NO implica compatibilidad ni entrenamiento comprobado.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from fresita_core import BASE

PREFIX = "FRESITA_UNSLOTH:"
PACKAGES = ("unsloth", "unsloth_zoo", "torch", "trl", "peft",
            "bitsandbytes", "triton", "triton-windows")
PROBE_SCRIPT = r"""
import importlib.metadata as metadata
import json
import struct
import sys

packages = {}
for name in ('unsloth', 'unsloth_zoo', 'torch', 'trl', 'peft',
             'bitsandbytes', 'triton', 'triton-windows'):
    try:
        packages[name] = metadata.version(name)
    except metadata.PackageNotFoundError:
        packages[name] = None

report = {
    'python': '.'.join(str(x) for x in sys.version_info[:3]),
    'bits': struct.calcsize('P') * 8,
    'packages': packages,
    'cuda_build': None,
    'cuda_available': False,
    'gpu': None,
    'torch_importable': False,
}
try:
    import torch
    report['torch_importable'] = True
    report['cuda_build'] = torch.version.cuda
    report['cuda_available'] = bool(torch.cuda.is_available())
    if report['cuda_available']:
        report['gpu'] = torch.cuda.get_device_name(0)
except Exception:
    pass
print('FRESITA_UNSLOTH:' + json.dumps(report, ensure_ascii=False))
"""

def parse_probe_output(output):
    if not isinstance(output, str) or len(output) > 200_000:
        raise ValueError("El diagnóstico de Unsloth devolvió datos inválidos.")
    matches = [line[len(PREFIX):] for line in output.splitlines()
               if line.startswith(PREFIX)]
    if len(matches) != 1:
        raise ValueError("Se esperaba un único reporte de Unsloth.")
    try:
        report = json.loads(matches[0])
    except (TypeError, ValueError) as exc:
        raise ValueError("El reporte de Unsloth no contiene JSON válido.") from exc
    if not isinstance(report, dict):
        raise ValueError("El reporte de Unsloth no es un objeto.")
    if (not isinstance(report.get("python"), str)
        or len(report["python"]) > 30
        or type(report.get("bits")) is not int
        or report["bits"] not in (32, 64)
        or type(report.get("cuda_available")) is not bool
        or type(report.get("torch_importable")) is not bool
        or not isinstance(report.get("packages"), dict)
        or set(report["packages"]) != set(PACKAGES)
        or any(value is not None and
               (not isinstance(value, str) or len(value) > 80)
               for value in report["packages"].values())
        or report.get("cuda_build") is not None and
           (not isinstance(report["cuda_build"], str)
            or len(report["cuda_build"]) > 30)
        or report.get("gpu") is not None and
           (not isinstance(report["gpu"], str) or len(report["gpu"]) > 100)):
        raise ValueError("El reporte de Unsloth tiene formato incompatible.")
    return report

def check_unsloth(*, workspace=None, runner=None, environment=".venv", python_override=None):
    """Inspecciona metadatos locales y disponibilidad CUDA; nunca instala paquetes."""
    if environment not in (".venv", ".venv-unsloth"):
        raise ValueError("Selecciona un entorno Unsloth permitido por Fresita.")
    root = Path(workspace) if workspace is not None else BASE
    python = Path(python_override) if python_override is not None else root / environment / "Scripts" / "python.exe"
    if not python.is_file():
        raise FileNotFoundError(
            "No existe el entorno de entrenamiento de Fresita. "
            "Prepáralo primero; esta consulta no instala Unsloth.")
    run = runner if runner is not None else subprocess.run
    try:
        result = run([str(python), "-I", "-c", PROBE_SCRIPT],
                     stdin=subprocess.DEVNULL, capture_output=True,
                     text=True, encoding="utf-8", errors="replace",
                     timeout=60,
                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError("El diagnóstico de Unsloth superó 60 segundos.") from exc
    if result.returncode != 0:
        raise RuntimeError(
            "No se pudo inspeccionar el entorno Python; revisa su instalación.")
    return parse_probe_output(result.stdout)

def format_unsloth_report(report):
    """Mostrar sólo datos de una lista permitida, nunca rutas ni mensajes privados."""
    packages = report["packages"]
    installed = packages["unsloth"] is not None
    lines = [
        "Unsloth: " + ("instalado (sin validar entrenamiento)" if installed
                       else "no instalado en el entorno de Fresita"),
        "Python: " + report["python"] + " (" + str(report["bits"]) + " bits)",
        "PyTorch: " + str(packages["torch"] or "no instalado"),
        "CUDA del wheel: " + str(report["cuda_build"] or "N/D"),
        "CUDA disponible: " + ("sí" if report["cuda_available"] else "no"),
        "GPU: " + str(report["gpu"] or "N/D"),
        "Unsloth Zoo: " + str(packages["unsloth_zoo"] or "no instalado"),
        "TRL: " + str(packages["trl"] or "no instalado"),
        "PEFT: " + str(packages["peft"] or "no instalado"),
        "bitsandbytes: " + str(packages["bitsandbytes"] or "no instalado"),
        "Triton: " + str(packages["triton"] or packages["triton-windows"] or "no instalado"),
        "",
        "Esta revisión sólo lee metadatos e interroga CUDA. No importa Unsloth,",
        "no descarga modelos y NO confirma compatibilidad de kernels,",
        "entrenamiento Unsloth ni ahorro de VRAM en la RTX 5060.",
        "TRL/PEFT es la opción predeterminada; Unsloth es experimental.",
        "No se instala Unsloth ni se modifica el entorno existente."
    ]
    return "\n".join(lines)
