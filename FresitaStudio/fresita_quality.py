"""Evaluación offline de predicciones. Nunca ejecuta código ni carga modelos."""
from __future__ import annotations
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata
from uuid import uuid4

MAX_BYTES = 8 * 1024 * 1024
MAX_ROWS = 5000
MAX_TEXT = 20000
CATEGORIES = ("es_mx", "codigo_python")

def _normal(text):
    """NFKC y espacios, sin eliminar acentos del español."""
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())

def _f1(reference, prediction):
    a = Counter(re.findall(r"\w+", _normal(reference), flags=re.UNICODE))
    b = Counter(re.findall(r"\w+", _normal(prediction), flags=re.UNICODE))
    if not a or not b:
        return 1.0 if a == b else 0.0
    common = sum((a & b).values())
    if not common:
        return 0.0
    precision = common / sum(b.values())
    recall = common / sum(a.values())
    return 2 * precision * recall / (precision + recall)

def evaluate_predictions(path):
    """JSONL con categoria, referencia, prediccion; sólo reporta agregados."""
    path = Path(path).expanduser().resolve(strict=True)
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("Selecciona un JSONL de hasta 8 MB")
    raw = path.read_bytes()
    lines = raw.decode("utf-8-sig").splitlines()
    if len(lines) > MAX_ROWS:
        raise ValueError("Máximo 5,000 filas por evaluación")
    stats = {k: {"n": 0, "exact": 0, "f1": 0.0, "syntax": 0} for k in CATEGORIES}
    invalid = 0
    for line in lines:
        try:
            row = json.loads(line)
        except (ValueError, TypeError):
            invalid += 1
            continue
        if not isinstance(row, dict):
            invalid += 1
            continue
        cat = row.get("categoria")
        ref = row.get("referencia")
        pred = row.get("prediccion")
        if (cat not in CATEGORIES or not isinstance(ref, str)
                or not isinstance(pred, str) or not ref.strip()
                or len(ref) > MAX_TEXT or len(pred) > MAX_TEXT):
            invalid += 1
            continue
        s = stats[cat]
        s["n"] += 1
        if cat == "es_mx":
            s["exact"] += _normal(ref) == _normal(pred)
            s["f1"] += _f1(ref, pred)
        else:
            # ast.parse sólo analiza sintaxis: NO ejecuta código.
            s["exact"] += ref.strip().replace("\r\n", "\n") == pred.strip().replace("\r\n", "\n")
            try:
                ast.parse(pred)
            except (SyntaxError, ValueError, RecursionError):
                pass
            else:
                s["syntax"] += 1
    total = sum(s["n"] for s in stats.values())
    if not total:
        raise ValueError("No hay filas válidas. Usa categoria, referencia y prediccion")
    es, code = stats["es_mx"], stats["codigo_python"]
    return {
        "esquema": 1,
        "tipo": "evaluacion_offline_predicciones",
        "sha256_entrada": hashlib.sha256(raw).hexdigest(),
        "ejemplos_validos": total,
        "filas_invalidas": invalid,
        "exactitud_total": round(sum(s["exact"] for s in stats.values()) / total, 4),
        "metricas": {
            "es_mx": {
                "ejemplos": es["n"],
                "exactitud_normalizada": round(es["exact"] / es["n"], 4) if es["n"] else None,
                "f1_tokens_promedio": round(es["f1"] / es["n"], 4) if es["n"] else None
            },
            "codigo_python": {
                "ejemplos": code["n"],
                "coincidencia_exacta": round(code["exact"] / code["n"], 4) if code["n"] else None,
                "sintaxis_valida": round(code["syntax"] / code["n"], 4) if code["n"] else None
            }
        },
        "advertencia": "No ejecuta ni verifica la corrección funcional del código."
    }

def save_quality_report(report, workspace):
    """Guarda sólo agregados, en archivo nuevo mediante reemplazo atómico."""
    if not isinstance(report, dict) or report.get("tipo") != "evaluacion_offline_predicciones":
        raise ValueError("Reporte inválido")
    folder = Path(workspace) / "experiments" / "evaluaciones"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / ("calidad-" + uuid4().hex + ".json")
    payload = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
    fd, temp = tempfile.mkstemp(prefix=".fresita-", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
        os.replace(temp, target)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return target

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluar predicciones sin ejecutar código")
    parser.add_argument("archivo", type=Path)
    parser.add_argument("--guardar-en", type=Path, default=None)
    args = parser.parse_args()
    result = evaluate_predictions(args.archivo)
    if args.guardar_en is not None:
        result["reporte_guardado"] = str(save_quality_report(result, args.guardar_en))
    print(json.dumps(result, ensure_ascii=False, indent=2))
