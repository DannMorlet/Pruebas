"""Diagnósticos seguros de memoria durante entrenamiento; no importa CUDA."""
from __future__ import annotations

import json
import sys

STAGES = frozenset(("carga", "preparacion", "entrenamiento", "evaluacion"))


def diagnose_memory_error(exc, stage):
    """Devuelve recomendaciones sin incluir rutas, prompts ni texto de la excepción."""
    if stage not in STAGES:
        raise ValueError("Etapa de entrenamiento desconocida")
    if isinstance(exc, MemoryError):
        return {
            "codigo": "RAM_AGOTADA", "etapa": stage,
            "acciones": [
                "Cierra aplicaciones que consuman RAM y revisa el archivo de paginación de Windows.",
                "Reduce el tamaño del modelo o de los lotes antes de repetir; no se modificaron los pesos originales.",
            ],
        }
    if not isinstance(exc, RuntimeError):
        return None
    message = str(exc).casefold()
    is_ram_oom = (
        "defaultcpuallocator: not enough memory" in message
        or "defaultcpuallocator: can\u0027t allocate memory" in message
        or "std::bad_alloc" in message
    )
    if is_ram_oom:
        return {
            "codigo": "RAM_AGOTADA", "etapa": stage,
            "acciones": [
                "Cierra aplicaciones que consuman RAM y revisa el archivo de paginación de Windows.",
                "Reduce el tamaño del modelo o de los lotes antes de repetir; no se modificaron los pesos originales.",
            ],
        }
    is_cuda_oom = (
        "cuda out of memory" in message
        or "cublas_status_alloc_failed" in message
        or "cudnn_status_alloc_failed" in message
        or "cudaerrormemoryallocation" in message
        or "cuda error: out of memory" in message
        or (type(exc).__name__ == "OutOfMemoryError"
            and type(exc).__module__.startswith("torch.cuda"))
    )
    if not is_cuda_oom:
        return None
    return {
        "codigo": "CUDA_SIN_VRAM", "etapa": stage,
        "acciones": [
            "Detén otras cargas de GPU y comprueba la VRAM libre; reinicia el proceso antes de reintentar.",
            "Para RTX 5060 de 8 GB, prueba un modelo menor o QLoRA compatible; reduce lote o longitud si sigue fallando.",
            "No se reintentó automáticamente ni se sobrescribieron los pesos originales.",
        ],
    }


def run_training_stage(stage, operation, *args, **kwargs):
    """Ejecuta una etapa sin reintentos automáticos y conserva la excepción original."""
    if stage not in STAGES:
        raise ValueError("Etapa de entrenamiento desconocida")
    try:
        return operation(*args, **kwargs)
    except (RuntimeError, MemoryError) as exc:
        diagnosis = diagnose_memory_error(exc, stage)
        if diagnosis is not None:
            print("FRESITA_DIAGNOSTICO: " + json.dumps(
                diagnosis, ensure_ascii=False), file=sys.stderr, flush=True)
        raise


def report_terminal_failure(exc):
    """Evita que el traceback final revele rutas privadas en errores de memoria.

    Devuelve True cuando se reconoció el error; el llamador debe salir con código 1.
    Los diagnósticos por etapa ya fueron emitidos por run_training_stage.
    """
    diagnosis = diagnose_memory_error(exc, "entrenamiento")
    if diagnosis is None:
        return False
    print("FRESITA_ERROR_FINAL: " + json.dumps(
        {"codigo": diagnosis["codigo"], "detalle": "Entrenamiento detenido por memoria insuficiente."},
        ensure_ascii=False), file=sys.stderr, flush=True)
    return True
