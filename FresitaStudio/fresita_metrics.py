"""Historial numérico de entrenamiento: sin textos ni dependencias de CUDA."""
import hashlib
import json
import math
import re
from pathlib import Path

KEYS=("loss","eval_loss")

def _number(value):
    if isinstance(value,bool) or not isinstance(value,(float,int)):
        return None
    value=float(value)
    return value if math.isfinite(value) else None

def append_metrics(path,step,logs):
    if type(step) is not int or step<0 or not isinstance(logs,dict):
        return False
    item={"paso":step}
    for key in KEYS:
        value=_number(logs.get(key))
        if value is not None:item[key]=value
    if len(item)==1:return False
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as f:
        f.write(json.dumps(item,ensure_ascii=False,allow_nan=False)+"\n")
    return True

def read_history(path):
    path=Path(path)
    if not path.is_file():return []
    if path.stat().st_size>2_000_000:raise ValueError("Historial demasiado grande (2 MB)")
    result=[]
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:obj=json.loads(line)
            except json.JSONDecodeError:continue
            if not isinstance(obj,dict) or type(obj.get("paso")) is not int or obj["paso"]<0:continue
            item={"paso":obj["paso"]}
            for key in KEYS:
                value=_number(obj.get(key))
                if value is not None:item[key]=value
            if len(item)>1:result.append(item)
    return result[-2000:]

def read_summary(folder):
    path=Path(folder)/"metricas_validacion.json"
    if not path.is_file():return {}
    if path.stat().st_size>20_000:raise ValueError("Reporte demasiado grande")
    try:obj=json.loads(path.read_text(encoding="utf-8"))
    except (ValueError,UnicodeError):return {}
    if not isinstance(obj,dict):return {}
    result={key:_number(obj.get(key)) for key in ("eval_loss","perplejidad")}
    for key in ("pasos_entrenamiento","ejemplos_validacion","eval_max_length"):
        value=obj.get(key)
        if type(value) is int and 0<=value<=1_000_000_000:result[key]=value
    for key in ("validation_sha256","tokenizer_sha256"):
        value=obj.get(key)
        if isinstance(value,str) and re.fullmatch(r"[0-9a-f]{64}",value):
            result[key]=value
    return result

def list_experiments(root,limit=50):
    root=Path(root)
    if not root.is_dir():return []
    items=[]
    for folder in sorted(root.iterdir(),key=lambda p:p.name,reverse=True):
        if folder.is_symlink() or not folder.is_dir():continue
        if (folder/"metricas_historial.jsonl").is_file() or (folder/"metricas_validacion.json").is_file():
            items.append(folder)
            if len(items)>=limit:break
    return items

def evaluation_fingerprints(dataset_path, tokenizer, max_length):
    """Huellas sin datos textuales para comparar evaluaciones bajo condiciones iguales.

    Si el tokenizador no ofrece serialización completa, no se declara comparable.
    """
    if type(max_length) is not int or not 1<=max_length<=1_000_000:
        raise ValueError("Longitud de evaluación inválida")
    dataset_hash=hashlib.sha256()
    path=Path(dataset_path)
    if path.stat().st_size>100*1024*1024:
        raise ValueError("Validación demasiado grande")
    with path.open("rb") as source:
        for chunk in iter(lambda:source.read(1024*1024),b""):
            dataset_hash.update(chunk)
    backend=getattr(tokenizer,"backend_tokenizer",None)
    fingerprint=None
    if backend is not None and callable(getattr(backend,"to_str",None)):
        raw=backend.to_str()
        if isinstance(raw,str):
            fingerprint=hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return {"validation_sha256":dataset_hash.hexdigest(),
            "tokenizer_sha256":fingerprint,"eval_max_length":max_length}


def compare_summaries(a,b):
    """Comparación conservadora: menor eval_loss sólo con evaluación equivalente."""
    if not isinstance(a,dict) or not isinstance(b,dict):
        return {"comparable":False,"motivo":"Reportes inválidos"}
    la,lb=_number(a.get("eval_loss")),_number(b.get("eval_loss"))
    if la is None or lb is None:
        return {"comparable":False,"motivo":"Falta una pérdida de validación válida"}
    for key,reason in (("validation_sha256","dataset de validación"),
                       ("tokenizer_sha256","tokenizador")):
        aa,bb=a.get(key),b.get(key)
        if not (isinstance(aa,str) and re.fullmatch(r"[0-9a-f]{64}",aa)
                and isinstance(bb,str) and re.fullmatch(r"[0-9a-f]{64}",bb)):
            return {"comparable":False,"motivo":f"Falta huella verificable de {reason} en uno de los experimentos"}
        if aa!=bb:
            return {"comparable":False,"motivo":f"Los experimentos usan distinto {reason}"}
    for key,reason in (("eval_max_length","longitud máxima de evaluación"),
                       ("ejemplos_validacion","número de ejemplos")):
        aa,bb=a.get(key),b.get(key)
        if type(aa) is not int or type(bb) is not int or aa<1 or bb<1:
            return {"comparable":False,"motivo":f"Falta {reason} verificable"}
        if aa!=bb:
            return {"comparable":False,"motivo":f"Difiere {reason}"}
    delta=lb-la
    winner="empate" if abs(delta)<=1e-9 else ("A" if delta>0 else "B")
    return {"comparable":True,"loss_a":la,"loss_b":lb,
            "delta_b_menos_a":delta,"mejor":winner,
            "nota":"Comparación orientativa de eval_loss; no certifica calidad de respuestas"}
