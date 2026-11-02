"""Diagnóstico local de LoRA/QLoRA desde Fresita.exe, sin entrenar ni instalar.

Ejecuta el worker en el Python del entorno aislado; no lee datasets ni
carga pesos. No utiliza shell y nunca transmite datos a la red.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from fresita_core import BASE

PREFIX = "DIAGNÓSTICO CUDA:"
REQUIRED_KEYS = ("ok", "cuda_disponible", "dependencias", "errores", "avisos")

def parse_preflight_output(output):
    """Acepta únicamente el reporte JSON estructurado del worker."""
    if not isinstance(output, str) or len(output) > 1_000_000:
        raise ValueError("El diagnóstico devolvió una respuesta inválida o demasiado grande.")
    reports = [line[len(PREFIX):].strip() for line in output.splitlines()
               if line.startswith(PREFIX)]
    if len(reports) != 1 or len(reports[0]) > 100_000:
        raise ValueError("No se recibió un reporte CUDA único y válido.")
    try:
        report = json.loads(reports[0])
    except (ValueError, TypeError) as exc:
        raise ValueError("El diagnóstico CUDA no devolvió JSON válido.") from exc
    if (not isinstance(report, dict)
            or not all(key in report for key in REQUIRED_KEYS)
            or type(report["ok"]) is not bool
            or type(report["cuda_disponible"]) is not bool
            or not isinstance(report["dependencias"], dict)
            or not isinstance(report["errores"], list)
            or not isinstance(report["avisos"], list)
            or not all(isinstance(x, str) for x in report["errores"] + report["avisos"])):
        raise ValueError("El reporte CUDA tiene un formato incompatible.")
    return report

def check_training_environment(qlora=False, *, workspace=None, bundle_root=None, runner=None, python_override=None):
    """Comprueba entorno Python de Fresita; no descarga ni ejecuta entrenamiento."""
    if type(qlora) is not bool:
        raise ValueError("El modo QLoRA debe ser booleano.")
    workspace = Path(workspace) if workspace is not None else BASE
    bundle_root = (Path(bundle_root) if bundle_root is not None else
                   Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)))
    python = Path(python_override) if python_override is not None else workspace / ".venv" / "Scripts" / "python.exe"
    worker = bundle_root / "workers" / "train_lora.py"
    if not python.is_file():
        raise FileNotFoundError(
            "Falta el Python de entrenamiento en Documentos/Fresita Studio/.venv. "
            "Instala Python 3.12 x64 y prepara el entorno siguiendo README.md.")
    if not worker.is_file():
        raise FileNotFoundError("No se encontró el worker de entrenamiento de Fresita.")
    run = runner if runner is not None else subprocess.run
    with tempfile.TemporaryDirectory(prefix="fresita-diagnostico-") as folder:
        recipe = Path(folder) / "preflight.json"
        recipe.write_text(json.dumps({"qlora": qlora}), encoding="utf-8")
        command = [str(python), str(worker), "--config", str(recipe), "--preflight"]
        try:
            result = run(command, stdin=subprocess.DEVNULL, capture_output=True,
                         text=True, encoding="utf-8", errors="replace", timeout=90,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError("El diagnóstico CUDA superó 90 segundos. No se entrenó.") from exc
    report = parse_preflight_output(result.stdout)
    if result.returncode != 0 and report["ok"]:
        raise RuntimeError("El proceso de diagnóstico falló después de comprobar CUDA.")
    return report

def format_preflight_report(report):
    """Muestra sólo campos estructurados; no muestra rutas, pesos ni datasets."""
    ok = report["ok"]
    lines = ["Entorno listo para intentar entrenar." if ok else
             "Entorno incompleto: no inicies el entrenamiento todavía.",
             "Este resultado NO prueba un entrenamiento real ni garantiza VRAM suficiente.",
             "",
             "Python: " + str(report.get("python") or "N/D"),
             "Arquitectura: " + str(report.get("bits") or "N/D") + " bits",
             "CUDA disponible: " + ("Sí" if report["cuda_disponible"] else "No"),
             "GPU: " + str(report.get("gpu") or "N/D"),
             "VRAM total: " + str(report.get("vram_total_mib") or "N/D") + " MiB",
             "VRAM libre (instantánea): " + str(report.get("vram_libre_mib") if
                                           report.get("vram_libre_mib") is not None else "N/D") + " MiB",
             "", "Dependencias:"]
    for name, version in sorted(report["dependencias"].items()):
        if name in ("torch","transformers","datasets","accelerate","peft","trl","safetensors","bitsandbytes"):
            lines.append("  " + name + ": " + str(version or "NO INSTALADO")[:60])
    if report["errores"]:
        lines.extend(["", "Problemas:"] + ["• " + x[:200] for x in report["errores"][:15]])
    if report["avisos"]:
        lines.extend(["", "Avisos:"] + ["• " + x[:200] for x in report["avisos"][:15]])
    return "\n".join(lines)
