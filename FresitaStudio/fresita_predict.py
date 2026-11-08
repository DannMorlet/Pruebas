"""Predicciones con API OpenAI-compatible sólo en 127.0.0.1, bajo solicitud."""
from __future__ import annotations
import hashlib
import http.client
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit
from uuid import uuid4

MAX_INPUT_BYTES=8*1024*1024
MAX_CASES=100
MAX_PROMPT=4000
MAX_REFERENCE=20000
MAX_PREDICTION=20000
MAX_RESPONSE_BYTES=1024*1024
CATEGORIES=frozenset(("es_mx","codigo_python"))

def local_server(endpoint: str) -> tuple[str,int]:
    try:
        url=urlsplit(endpoint)
        port=url.port
    except ValueError as exc:
        raise ValueError("Puerto o URL local inválida") from exc
    if (url.scheme!="http" or url.hostname!="127.0.0.1"
            or not isinstance(port,int) or not 1<=port<=65535
            or url.path.rstrip("/")!="/v1" or url.query or url.fragment
            or url.username is not None or url.password is not None):
        raise ValueError("Sólo se permite http://127.0.0.1:PUERTO/v1")
    return "127.0.0.1",port

def read_cases(path: Path) -> list[dict[str,str]]:
    path=Path(path).expanduser().resolve(strict=True)
    if not path.is_file() or path.stat().st_size>MAX_INPUT_BYTES:
        raise ValueError("Selecciona un JSONL de hasta 8 MB")
    cases=[]
    with path.open("r",encoding="utf-8-sig") as stream:
        for lineno,line in enumerate(stream,1):
            if not line.strip():continue
            if len(cases)>=MAX_CASES:
                raise ValueError("Máximo 100 preguntas por lote")
            try:row=json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSONL inválido en línea {lineno}") from exc
            if not isinstance(row,dict):
                raise ValueError(f"La línea {lineno} debe ser un objeto")
            prompt,reference,category=(row.get(k) for k in ("pregunta","referencia","categoria"))
            if (not isinstance(prompt,str) or not prompt.strip() or len(prompt)>MAX_PROMPT
                    or not isinstance(reference,str) or not reference.strip()
                    or len(reference)>MAX_REFERENCE or category not in CATEGORIES):
                raise ValueError(f"La línea {lineno} requiere pregunta, referencia y categoria válidas")
            cases.append({"pregunta":prompt,"referencia":reference,"categoria":category})
    if not cases:raise ValueError("El archivo no contiene preguntas válidas")
    return cases

def ask_local(host: str,port: int,model: str,prompt: str,max_tokens: int,timeout: float=45.0) -> str:
    body=json.dumps({"model":model,"messages":[{"role":"user","content":prompt}],
                     "temperature":0,"max_tokens":max_tokens},ensure_ascii=False).encode("utf-8")
    conn=http.client.HTTPConnection(host,port,timeout=timeout)
    try:
        conn.request("POST","/v1/chat/completions",body=body,
                     headers={"Content-Type":"application/json","Accept":"application/json"})
        response=conn.getresponse()
        raw=response.read(MAX_RESPONSE_BYTES+1)
        if len(raw)>MAX_RESPONSE_BYTES:
            raise ValueError("Respuesta del servidor local demasiado grande")
        if response.status!=200:
            raise ValueError(f"El servidor local respondió HTTP {response.status}")
        try:
            obj=json.loads(raw)
            content=obj["choices"][0]["message"]["content"]
        except (ValueError,KeyError,IndexError,TypeError) as exc:
            raise ValueError("Respuesta incompatible con chat/completions") from exc
        if not isinstance(content,str) or not content.strip() or len(content)>MAX_PREDICTION:
            raise ValueError("Predicción vacía, no textual o demasiado larga")
        return content
    finally:
        conn.close()

def generate_predictions(dataset: Path,output_dir: Path,*,endpoint: str,
                         model: str,max_tokens: int=256,
                         cancelled=None,progress=None,requester=ask_local) -> tuple[Path,dict]:
    host,port=local_server(endpoint)
    if not isinstance(model,str) or not model.strip() or len(model)>256:
        raise ValueError("Selecciona un identificador de modelo válido")
    if isinstance(max_tokens,bool) or not isinstance(max_tokens,int) or not 1<=max_tokens<=512:
        raise ValueError("max_tokens debe estar entre 1 y 512")
    cases=read_cases(dataset)
    output_dir=Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True,exist_ok=True)
    final=output_dir/("predicciones-"+uuid4().hex+".jsonl")
    fd,temp=tempfile.mkstemp(prefix=".fresita-",suffix=".tmp",dir=output_dir)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as stream:
            for i,case in enumerate(cases,1):
                if cancelled is not None and cancelled():
                    raise InterruptedError("Generación cancelada; no se guardaron resultados parciales")
                prediction=requester(host,port,model,case["pregunta"],max_tokens)
                if not isinstance(prediction,str) or not prediction.strip() or len(prediction)>MAX_PREDICTION:
                    raise ValueError("El servidor devolvió una predicción inválida")
                stream.write(json.dumps({"categoria":case["categoria"],
                                         "referencia":case["referencia"],
                                         "prediccion":prediction},ensure_ascii=False)+"\n")
                if progress is not None:progress(i,len(cases))
        if cancelled is not None and cancelled():
            raise InterruptedError("Generación cancelada; no se guardaron resultados parciales")
        os.replace(temp,final)
    finally:
        if os.path.exists(temp):os.unlink(temp)
    summary={"ejemplos":len(cases),"modelo":model,
             "sha256_predicciones":hashlib.sha256(final.read_bytes()).hexdigest(),
             "advertencia":"El JSONL contiene referencias y predicciones privadas: no subir a GitHub."}
    return final,summary

def main():
    import argparse
    from fresita_quality import evaluate_predictions,save_quality_report
    parser=argparse.ArgumentParser(description="Generar predicciones sólo con servidor local")
    parser.add_argument("archivo",type=Path)
    parser.add_argument("--modelo",required=True)
    parser.add_argument("--endpoint",default="http://127.0.0.1:1234/v1")
    parser.add_argument("--salida",type=Path,
                        default=Path.home()/"Documents"/"Fresita Studio"/"experiments"/"predicciones")
    parser.add_argument("--max-tokens",type=int,default=256)
    args=parser.parse_args()
    out,summary=generate_predictions(args.archivo,args.salida,endpoint=args.endpoint,
                                    model=args.modelo,max_tokens=args.max_tokens,
                                    progress=lambda i,n:print(f"Completadas {i}/{n}",flush=True))
    report=evaluate_predictions(out)
    saved=save_quality_report(report,args.salida.parent.parent)
    print(json.dumps({"archivo_privado":str(out),"resumen":summary,
                      "reporte":str(saved),"metricas":report["metricas"]},
                     ensure_ascii=False,indent=2))

if __name__=="__main__":main()
