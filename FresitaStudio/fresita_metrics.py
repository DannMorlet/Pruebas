"""Historial numérico de entrenamiento: sin textos ni dependencias de CUDA."""
import json
import math
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
    for key in ("pasos_entrenamiento","ejemplos_validacion"):
        value=obj.get(key)
        if type(value) is int and 0<=value<=1_000_000_000:result[key]=value
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
