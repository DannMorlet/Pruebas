"""Diagnóstico de entrenamiento sin descargar pesos ni leer datasets privados."""
from __future__ import annotations

import importlib
from importlib import metadata
import struct
import sys

REQUIRED = ("torch", "transformers", "datasets", "accelerate", "peft", "trl", "safetensors")


def inspect_environment(qlora=False, *, version_lookup=None, torch_module=None):
    """Verifica dependencias y CUDA; no asegura que un modelo quepa en VRAM."""
    if type(qlora) is not bool:
        raise ValueError("qlora debe ser booleano")
    lookup = version_lookup if version_lookup is not None else metadata.version
    report = {
        "ok": True,
        "python": ".".join(map(str, sys.version_info[:3])),
        "bits": struct.calcsize("P") * 8,
        "dependencias": {},
        "cuda_disponible": False,
        "gpu": None,
        "vram_total_mib": None,
        "errores": [],
        "avisos": [],
    }
    if report["bits"] != 64:
        report["errores"].append("Se requiere Python x64 para entrenar.")
    if sys.version_info[:2] != (3, 12):
        report["avisos"].append("Python 3.12 x64 es la versión recomendada para este proyecto.")
    for package in REQUIRED + (("bitsandbytes",) if qlora else ()):
        try:
            report["dependencias"][package] = str(lookup(package))
        except metadata.PackageNotFoundError:
            report["dependencias"][package] = None
            report["errores"].append("Falta la dependencia: " + package)
        except (ValueError, OSError) as exc:
            report["dependencias"][package] = None
            report["errores"].append("No se pudo consultar " + package + ": " + type(exc).__name__)
    if report["dependencias"]["torch"] is not None:
        try:
            torch = torch_module if torch_module is not None else importlib.import_module("torch")
            if torch.cuda.is_available():
                report["cuda_disponible"] = True
                report["gpu"] = str(torch.cuda.get_device_name(0))[:100]
                props = torch.cuda.get_device_properties(0)
                report["vram_total_mib"] = int(props.total_memory) // (1024 * 1024)
                if report["vram_total_mib"] < 8192:
                    report["avisos"].append("VRAM limitada: reduce longitud, lote o tamaño del modelo si hay OOM.")
            else:
                report["errores"].append("PyTorch no detecta una GPU CUDA disponible.")
        except (ImportError, OSError, RuntimeError, AttributeError, ValueError) as exc:
            report["errores"].append("No se pudo inicializar CUDA: " + type(exc).__name__)
    if qlora and report["dependencias"].get("bitsandbytes") is not None:
        report["avisos"].append("bitsandbytes instalado: falta verificar su compatibilidad real con CUDA/Windows y el modelo.")
    report["avisos"].append("Este diagnóstico no carga pesos, no prueba entrenamiento y no garantiza memoria suficiente.")
    report["ok"] = not report["errores"]
    return report
