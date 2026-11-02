"""Benchmark local: latencia y tokens reportados, sin guardar preguntas."""
from __future__ import annotations
import argparse
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import statistics
import tempfile
import time
from uuid import uuid4
from fresita_predict import generate_predictions, local_server, MAX_RESPONSE_BYTES, MAX_PREDICTION
from fresita_resources import ResourceSampler

def request_usage(host, port, model, prompt, max_tokens):
    """Sólo HTTP loopback. No se estima usage si el servidor no lo proporciona."""
    if host != "127.0.0.1" or type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("Servidor no local")
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0, "max_tokens": max_tokens},
                      ensure_ascii=False).encode("utf-8")
    conn = http.client.HTTPConnection(host, port, timeout=45)
    try:
        conn.request("POST", "/v1/chat/completions", body=body,
                     headers={"Content-Type": "application/json", "Accept": "application/json"})
        response = conn.getresponse()
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("Respuesta local demasiado grande")
        if response.status != 200:
            raise ValueError(f"Servidor local HTTP {response.status}")
        try:
            obj = json.loads(raw)
            answer = obj["choices"][0]["message"]["content"]
        except (ValueError, TypeError, KeyError, IndexError) as exc:
            raise ValueError("Respuesta local incompatible") from exc
        if not isinstance(answer, str) or not answer.strip() or len(answer) > MAX_PREDICTION:
            raise ValueError("Predicción local inválida")
        usage = obj.get("usage")
        tokens = usage.get("completion_tokens") if isinstance(usage, dict) else None
        if type(tokens) is not int or not 0 <= tokens <= 1000000:
            tokens = None
        return answer, tokens
    finally:
        conn.close()

def summarize_speed(durations, token_counts):
    if not durations or len(durations) != len(token_counts):
        raise ValueError("Muestras de velocidad inválidas")
    if any(type(t) not in (int, float) or not math.isfinite(t) or t <= 0 for t in durations):
        raise ValueError("Duraciones inválidas")
    known = [t for t in token_counts if type(t) is int and 0 <= t <= 1000000]
    complete = len(known) == len(token_counts)
    total = sum(durations)
    sorted_times = sorted(durations)
    return {
        "tipo": "benchmark_velocidad_local",
        "esquema": 1,
        "muestras": len(durations),
        "latencia_media_s": round(statistics.mean(durations), 4),
        "latencia_p95_s": round(sorted_times[math.ceil(len(durations)*0.95)-1], 4),
        "tiempo_solicitudes_s": round(total, 4),
        "muestras_con_usage": len(known),
        "tokens_salida_reportados": sum(known) if complete else None,
        "tokens_salida_por_s_extremo_a_extremo": round(sum(known)/total, 3) if complete else None,
        "advertencia": "Tokens/s incluye prefill y HTTP; no es velocidad pura de decodificacion. No mide VRAM."
    }

def benchmark_local(dataset, output_dir, *, workspace, endpoint, model,
                    max_tokens=256, cancelled=None, progress=None,
                    requester=request_usage, clock=time.perf_counter,
                    sampler_factory=ResourceSampler):
    """Predicciones privadas y reporte agregado; no deja reporte parcial al cancelar."""
    local_server(endpoint)
    durations, tokens = [], []
    def measured(host, port, model_id, prompt, limit):
        start = clock()
        answer, count = requester(host, port, model_id, prompt, limit)
        duration = clock() - start
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("Reloj de benchmark inválido")
        durations.append(duration)
        tokens.append(count)
        return answer
    sampler = sampler_factory()
    sampler.start()
    try:
        output, summary = generate_predictions(dataset, output_dir, endpoint=endpoint,
            model=model, max_tokens=max_tokens, cancelled=cancelled, progress=progress,
            requester=measured)
    finally:
        resources = sampler.stop()
    report = summarize_speed(durations, tokens)
    report.update(resources)
    report["sha256_predicciones"] = summary["sha256_predicciones"]
    folder = Path(workspace)/"experiments"/"velocidad"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder/("velocidad-"+uuid4().hex+".json")
    fd, tmp = tempfile.mkstemp(prefix=".fresita-", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return output, target, report

def main():
    parser = argparse.ArgumentParser(description="Medir inferencia local sin enviar referencias")
    parser.add_argument("archivo", type=Path, help="JSONL de preguntas/referencias")
    parser.add_argument("--modelo", required=True)
    parser.add_argument("--endpoint", default="http://127.0.0.1:1234/v1")
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--workspace", type=Path,
                        default=Path.home()/"Documents"/"Fresita Studio")
    args = parser.parse_args()
    output, report_path, report = benchmark_local(
        args.archivo, args.workspace/"experiments"/"predicciones",
        workspace=args.workspace, endpoint=args.endpoint,
        model=args.modelo, max_tokens=args.max_tokens)
    print(json.dumps({"predicciones_privadas": str(output),
                      "reporte": str(report_path), "metricas": report},
                     ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
