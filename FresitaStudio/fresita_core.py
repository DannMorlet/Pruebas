"""Datos locales y herramientas puras de Fresita. No carga TensorFlow/PyTorch."""
from __future__ import annotations
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

BASE=Path(os.environ.get("FRESITA_HOME",str(Path.home()/"Documents"/"Fresita Studio")))

def init_workspace():
    for name in ("datasets","models","experiments","exports"):
        (BASE/name).mkdir(parents=True,exist_ok=True)

def slug(name):
    return re.sub("[^a-zA-Z0-9_-]+","-",name).strip("-")[:48] or "sin-nombre"

def normalize(row):
    if isinstance(row,str):return row.strip()
    if not isinstance(row,dict):return ""
    if isinstance(row.get("text"),str):return row["text"].strip()
    if isinstance(row.get("messages"),list):
        return "\n".join(f"{str(x.get('role', 'mensaje'))}: {x['content']}" for x in row["messages"] if isinstance(x,dict) and isinstance(x.get("content"),str))
    a=next((row.get(x) for x in ("instruction","prompt","question","pregunta") if row.get(x)),None)
    b=next((row.get(x) for x in ("output","response","answer","respuesta") if row.get(x)),None)
    return f"Usuario: {a}\nAsistente: {b}" if isinstance(a,str) and isinstance(b,str) else ""

def unique_file(name):
    init_workspace()
    path=BASE/"datasets"/(slug(name)+".jsonl")
    i=2
    while path.exists():
        path=BASE/"datasets"/(slug(name)+f"-{i}.jsonl")
        i+=1
    return path

def import_dataset(path):
    path=Path(path).expanduser().resolve(strict=True)
    if path.stat().st_size>100*1024*1024:raise ValueError("El máximo permitido es 100 MB")
    suffix=path.suffix.lower()
    if suffix==".jsonl":
        items=[]
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if line.strip():
                try:items.append(json.loads(line))
                except json.JSONDecodeError:continue
    elif suffix==".json":
        items=json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(items,dict):items=items.get("data",[items])
    elif suffix==".csv":
        with path.open(encoding="utf-8-sig",newline="") as f:items=list(csv.DictReader(f))
    elif suffix==".txt":
        items=path.read_text(encoding="utf-8-sig").split("\n\n")
    else:raise ValueError("Usa JSONL, JSON, CSV o TXT")
    if not isinstance(items,list):raise ValueError("Estructura de datos inválida")
    rows=[v for row in items if len(v:=normalize(row))>=8]
    if not rows:raise ValueError("No encontré ejemplos utilizables")
    target=unique_file(path.stem)
    with target.open("x",encoding="utf-8") as f:
        for row in rows:f.write(json.dumps({"text":row},ensure_ascii=False)+"\n")
    return target,len(rows)

def clean_dataset(path):
    path=Path(path).resolve(strict=True)
    if path.suffix.lower()!=".jsonl":raise ValueError("Se necesita JSONL normalizado")
    if path.stat().st_size>100*1024*1024:raise ValueError("Máximo 100 MB")
    clean=[];seen=set()
    for line in path.read_text(encoding="utf-8").splitlines():
        try:item=json.loads(line)
        except json.JSONDecodeError:continue
        if not isinstance(item,dict) or not isinstance(item.get("text"),str):continue
        value=item["text"].strip();key=" ".join(value.casefold().split())
        if len(value)<8 or key in seen:continue
        seen.add(key);clean.append(value)
    if not clean:raise ValueError("No quedaron ejemplos")
    target=unique_file(path.stem+"-limpio")
    with target.open("x",encoding="utf-8") as f:
        for value in clean:f.write(json.dumps({"text":value},ensure_ascii=False)+"\n")
    return target,len(clean)


def _iter_dataset_text(path):
    """Lee JSONL normalizado, sin ejecutar código ni descargar datos."""
    path=Path(path).expanduser().resolve(strict=True)
    if path.suffix.lower()!=".jsonl":
        raise ValueError("Se necesita un archivo JSONL")
    if not path.is_file() or path.stat().st_size>100*1024*1024:
        raise ValueError("El archivo debe existir y medir como máximo 100 MB")
    with path.open("r",encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                item=json.loads(line)
            except json.JSONDecodeError:
                yield None
                continue
            text=item.get("text") if isinstance(item,dict) else None
            yield text.strip() if isinstance(text,str) and len(text.strip())>=8 else None


def _fingerprint(text):
    return hashlib.sha256(" ".join(text.casefold().split()).encode("utf-8")).hexdigest()


def audit_dataset(path):
    """Métricas locales de calidad; nunca incluye ejemplos ni secretos en el reporte."""
    stats={"validos":0,"unicos":0,"duplicados":0,"invalidos":0,
           "caracteres_min":0,"caracteres_max":0,"caracteres_promedio":0}
    seen=set()
    total_chars=0
    for value in _iter_dataset_text(path):
        if value is None:
            stats["invalidos"]+=1
            continue
        stats["validos"]+=1
        length=len(value)
        total_chars+=length
        if stats["caracteres_min"]==0 or length<stats["caracteres_min"]:
            stats["caracteres_min"]=length
        stats["caracteres_max"]=max(stats["caracteres_max"],length)
        key=_fingerprint(value)
        if key in seen:
            stats["duplicados"]+=1
        else:
            seen.add(key)
            stats["unicos"]+=1
    if stats["validos"]:
        stats["caracteres_promedio"]=round(total_chars/stats["validos"])
    return stats


def split_dataset(path,percent=10):
    """Genera dos copias sin duplicados y sin fuga entre entrenamiento y validación.

    Selección reproducible por SHA-256 del texto normalizado. No entrena ni
    evalúa modelos: prepara datos independientes para una evaluación posterior.
    """
    if not isinstance(percent,int) or not 5<=percent<=30:
        raise ValueError("La validación debe ocupar entre 5% y 30%")
    rows={}
    for value in _iter_dataset_text(path):
        if value is None:
            raise ValueError("Hay filas inválidas: importa o limpia el dataset primero")
        rows.setdefault(_fingerprint(value),value)
    if len(rows)<10:
        raise ValueError("Se requieren al menos 10 ejemplos únicos para separar validación")
    ordered=sorted(rows.items())
    nval=max(1,len(ordered)*percent//100)
    valid=ordered[:nval]
    train=ordered[nval:]
    name=Path(path).stem
    train_path=unique_file(name+"-entrenamiento")
    valid_path=unique_file(name+"-validacion")
    for target,items in ((train_path,train),(valid_path,valid)):
        with target.open("x",encoding="utf-8") as output:
            for _,value in items:
                output.write(json.dumps({"text":value},ensure_ascii=False)+"\n")
    return train_path,valid_path,len(train),len(valid)

def inspect_safetensors(folder):
    folder=Path(folder).resolve(strict=True)
    files=list(folder.glob("*.safetensors"))
    if not files:raise ValueError("No hay archivos .safetensors")
    total=0
    for path in files:
        with path.open("rb") as f:
            prefix=f.read(8)
            if len(prefix)!=8:raise ValueError("Archivo de pesos inválido")
            n=int.from_bytes(prefix,"little")
            if n<2 or n>50_000_000:raise ValueError("Header inválido o demasiado grande")
            hdr=json.loads(f.read(n))
        for k,obj in hdr.items():
            if k=="__metadata__":continue
            if isinstance(obj,dict) and isinstance(obj.get("shape"),list):
                shape=obj["shape"]
                if all(isinstance(d,int) and d>=0 for d in shape):total+=math.prod(shape)
    return total,len(files)

def save_recipe(recipe):
    init_workspace()
    key="job-"+time.strftime("%Y%m%d-%H%M%S")+"-"+str(time.time_ns()%1_000_000)
    path=BASE/"experiments"/(key+".json")
    path.write_text(json.dumps(recipe,indent=2,ensure_ascii=False),encoding="utf-8")
    return path

def gpu_summary():
    exe=shutil.which("nvidia-smi")
    if not exe:return "GPU: nvidia-smi no disponible"
    try:
        out=subprocess.run([exe,"--query-gpu=name,memory.used,memory.total","--format=csv,noheader,nounits"],
                           capture_output=True,text=True,timeout=5,check=True).stdout.strip().splitlines()[0]
        name,used,total=[x.strip() for x in out.split(",")[:3]]
        return f"{name[:26]} · {used}/{total} MB"
    except (OSError,subprocess.SubprocessError,IndexError):return "GPU: no disponible"
