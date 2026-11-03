"""Actualizador transaccional, opt-in y sin instaladores del driver NVIDIA.

Versiona entornos Python completos y sólo conmuta el puntero activo después
de comprobar dependencias, CUDA y operación básica real en GPU (si hay GPU).
Nunca edita un entorno anterior, datasets, modelos, pesos ni drivers.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from urllib.request import Request, urlopen

from fresita_core import BASE
from fresita_updates import load_auto_install, load_settings
from fresita_train_setup import build_setup_plan, run_setup
from fresita_unsloth_setup import build_unsloth_setup_plan, run_unsloth_setup
from fresita_llama import latest_compatible_release, installed_server, install_release

TORCH_PROFILE = "torch-2.14.1-cu132-r1"
COMPONENTS = ("llama", "trl", "unsloth")
MIN_DRIVER = {"llama":615, "trl":595, "unsloth":595}
CHECK_INTERVAL = 24 * 60 * 60

class UpdateSkipped(RuntimeError):
    """Requisitos ausentes: no se modificó ningún entorno activo."""

def managed_root(root=None):
    return Path(root) if root is not None else BASE

def registry_path(root=None):
    return managed_root(root) / "config" / "componentes_activos.json"

def _safe_tag(tag):
    if not isinstance(tag, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,75}", tag):
        raise ValueError("Identificador de versión inválido")
    if tag in (".", ".."):
        raise ValueError("Versión inválida")
    return tag

def _load_registry(root=None):
    try:
        raw = json.loads(registry_path(root).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Registro inválido")
        entries = {}
        for comp in COMPONENTS:
            d = raw.get(comp,{})
            if not isinstance(d,dict):
                continue
            a=d.get("active"); p=d.get("previous")
            entries[comp]={"active":_safe_tag(a) if a is not None else None,
                           "previous":_safe_tag(p) if p is not None else None}
        return entries
    except (OSError, ValueError, TypeError):
        return {comp:{"active":None,"previous":None} for comp in COMPONENTS}

def _save_registry(data,root=None):
    path=registry_path(root)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=None
    try:
        with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,
              prefix=".componentes-",suffix=".tmp",delete=False) as file:
            tmp=Path(file.name)
            json.dump(data,file,ensure_ascii=False,indent=2)
            file.write("\n")
        os.replace(tmp,path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)

def component_dir(component,tag,root=None):
    if component not in COMPONENTS:
        raise ValueError("Componente no permitido")
    _safe_tag(tag)
    if component=="llama":
        return managed_root(root)/"motores"/"llama"/tag
    return managed_root(root)/"motores"/"entornos"/component/tag

def _valid_install(component,tag,root=None):
    if component in ("trl","unsloth") and tag=="legacy":
        env=".venv" if component=="trl" else ".venv-unsloth"
        folder=managed_root(root)/env
        binary=folder/"Scripts"/"python.exe"
        return binary.is_file() and not folder.is_symlink() and not binary.is_symlink()
    folder=component_dir(component,tag,root)
    if folder.is_symlink():
        return False
    if component=="llama":
        return (folder/"fresita_llama_manifest.json").is_file() and bool(list(folder.rglob("llama-server.exe")))
    env=".venv" if component=="trl" else ".venv-unsloth"
    p=folder/env/"Scripts"/"python.exe"
    return p.is_file() and not p.is_symlink()

def active_tag(component,root=None):
    tag=_load_registry(root)[component]["active"]
    return tag if tag and _valid_install(component,tag,root) else None

def active_python(component,root=None):
    if component not in ("trl","unsloth"):
        raise ValueError("Sólo entornos Python")
    tag=active_tag(component,root)
    if tag and tag!="legacy":
        env=".venv" if component=="trl" else ".venv-unsloth"
        return component_dir(component,tag,root)/env/"Scripts"/"python.exe"
    # Instalaciones manuales originales conservadas como respaldo.
    legacy=".venv" if component=="trl" else ".venv-unsloth"
    return managed_root(root)/legacy/"Scripts"/"python.exe"

def active_llama(root=None):
    tag=active_tag("llama",root)
    if tag:
        folder=component_dir("llama",tag,root)
        p=list(folder.rglob("llama-server.exe"))
        if len(p)==1:
            return p[0],tag
    # Compatibilidad con instalaciones preexistentes sin puntero.
    if root is None:
        return installed_server()
    return None

def activate(component,tag,root=None):
    if not _valid_install(component,tag,root):
        raise ValueError("No se activará una instalación incompleta")
    data=_load_registry(root)
    old=data[component]["active"]
    if old is None and component in ("trl","unsloth") and _valid_install(component,"legacy",root):
        old="legacy"
    if old != tag:
        data[component]={"active":tag,"previous":old}
        _save_registry(data,root)
    return tag

def rollback(component,root=None):
    if component not in COMPONENTS:
        raise ValueError("Componente no permitido")
    data=_load_registry(root)
    previous=data[component]["previous"]
    if not previous or not _valid_install(component,previous,root):
        raise ValueError("No existe una versión anterior verificada para restaurar")
    current=data[component]["active"]
    data[component]={"active":previous,"previous":current}
    _save_registry(data,root)
    return previous

def driver_major(runner=None):
    run=runner or subprocess.run
    try:
        result=run(["nvidia-smi","--query-gpu=driver_version",
                    "--format=csv,noheader"],capture_output=True,
                    text=True,timeout=8,check=True)
        value=result.stdout.strip().splitlines()[0].strip()
        match=re.fullmatch(r"(\d+)\.\d+(?:\.\d+)?",value)
        return int(match.group(1)) if match else None
    except (OSError,IndexError,subprocess.SubprocessError,AttributeError):
        return None

def cuda_smoke(python, *, unsloth=False, run=None):
    """Valida ejecución CUDA mínima con la GPU real, sin descargar modelos."""
    # Unsloth debe parchear el runtime ANTES de importar PyTorch.
    # Importarlo después de usar CUDA puede dejar kernels sin parchear.
    prefix = "import unsloth\n" if unsloth else ""
    code = prefix + ("import torch\n"
      "assert torch.cuda.is_available(), 'Sin GPU CUDA'\n"
      "x=torch.ones((32,32),device='cuda')\n"
      "y=(x @ x).sum().item()\n"
      "assert abs(y - 32768)<1, 'Resultado CUDA incorrecto'\n"
      "torch.cuda.synchronize()\n")
    if run is None:
        run=subprocess.run
    result=run([str(python),"-I","-c",code],stdin=subprocess.DEVNULL,
               stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
               timeout=180,check=False,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    if result.returncode != 0:
        raise UpdateSkipped("No pasó la prueba de CUDA real; se conservó el entorno anterior")

def _get_unsloth_version(opener=urlopen):
    req=Request("https://pypi.org/pypi/unsloth/json",
                headers={"User-Agent":"FresitaStudio/actualizaciones"})
    with opener(req,timeout=12) as response:
        payload=response.read(2_000_001)
    if len(payload)>2_000_000:
        raise ValueError("Metadatos PyPI demasiado grandes")
    version=json.loads(payload).get("info",{}).get("version")
    if not isinstance(version,str) or not re.fullmatch(r"[0-9][A-Za-z0-9.+-]{0,55}",version):
        raise ValueError("Versión PyPI no válida")
    return version

def _report(progress,msg):
    if progress: progress(msg)

def update_component(component, *, root=None, bundle_root=None, cancel=None,
                     progress=None, setup_runner=None, smoke_runner=None,
                     release=None, unsloth_version=None, platform=None, driver=None):
    """Instala un candidato aislado, valida GPU, conmuta; jamás reemplaza un venv.
    setup_runner y smoke_runner permiten CI completamente offline.
    """
    if component not in COMPONENTS:
        raise ValueError("Componente no permitido")
    if (platform if platform is not None else os.name)!="nt":
        raise UpdateSkipped("Actualizaciones automáticas sólo en Windows x64")
    if cancel is not None and cancel.is_set():
        raise UpdateSkipped("Actualización cancelada")
    if driver is None:
        driver=driver_major()
    if driver is None or driver<MIN_DRIVER[component]:
        raise UpdateSkipped(
            f"Driver NVIDIA no confirmado o insuficiente para {component}; no se instalará")
    root=managed_root(root)
    if component=="llama":
        release=release or latest_compatible_release()
        tag=_safe_tag(release["tag"])
        installed=active_tag("llama",root)
        if installed and int(installed[1:])>=int(tag[1:]):
            return f"llama.cpp ya está al día ({installed})"
        if cancel is not None and cancel.is_set():
            raise UpdateSkipped("Actualización cancelada")
        _report(progress,"Descargando motor oficial llama.cpp "+tag)
        if not _valid_install("llama",tag,root):
            install_release(release,root=root/"motores"/"llama",progress=progress)
        if cancel is not None and cancel.is_set():
            raise UpdateSkipped("Versión descargada sin activar (cancelada)")
        activate("llama",tag,root)
        return f"llama.cpp {tag} instalado con SHA-256 y activado"
    if component=="trl":
        tag=TORCH_PROFILE
    else:
        version=unsloth_version or _get_unsloth_version()
        tag=_safe_tag("unsloth-"+version.replace("+","_"))
    if active_tag(component,root)==tag:
        return f"{component} ya está al día ({tag})"
    folder=component_dir(component,tag,root)
    folder.parent.mkdir(parents=True,exist_ok=True)
    if folder.is_symlink() or folder.exists() and not _valid_install(component,tag,root):
        raise UpdateSkipped("Hay una instalación incompleta; requiere revisión sin borrado automático")
    if not folder.exists():
        folder.mkdir()
        try:
            _report(progress,f"Preparando entorno aislado {component} (varios GB)")
            if component=="trl":
                plan=build_setup_plan(qlora=True,workspace=folder,bundle_root=bundle_root)
                run_setup(plan,runner=setup_runner,cancel=cancel,
                          on_stage=progress,platform="nt")
            else:
                plan=build_unsloth_setup_plan(workspace=folder)
                # Se fija explícitamente la versión publicada por PyPI.
                for _,cmd in plan["commands"]:
                    if "unsloth" in cmd and cmd[:3]==["uv","pip","install"]:
                        cmd[cmd.index("unsloth")]="unsloth=="+version
                run_unsloth_setup(plan,runner=setup_runner,cancel=cancel,
                                  on_stage=progress,platform="nt")
        except Exception:
            # El instalador limpia sólo el .venv nuevo en caso de error.
            # No borrar otros archivos porque pueden estar bloqueados.
            raise
    env=".venv" if component=="trl" else ".venv-unsloth"
    python=folder/env/"Scripts"/"python.exe"
    _report(progress,f"Probando CUDA físicamente en {component}")
    cuda_smoke(python,unsloth=(component=="unsloth"),run=smoke_runner)
    if cancel is not None and cancel.is_set():
        raise UpdateSkipped("Verificación terminada, activación cancelada")
    activate(component,tag,root)
    return f"{component} {tag} instalado, probado en CUDA y activado"

def update_due(root=None, now=None):
    """Limita comprobaciones automáticas a una vez por 24 horas."""
    root=managed_root(root)
    path=root/"config"/"ultima_busqueda_actualizaciones.json"
    now=dt.datetime.now(dt.timezone.utc) if now is None else now
    try:
        data=json.loads(path.read_text(encoding="utf-8"))
        last=dt.datetime.fromisoformat(data["comprobado_utc"])
        if last.tzinfo and dt.timedelta(0)<=now-last<dt.timedelta(seconds=CHECK_INTERVAL):
            return False
    except (OSError,ValueError,TypeError,KeyError):
        pass
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=None
    try:
        with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,
              prefix=".busqueda-",delete=False) as file:
            tmp=Path(file.name)
            json.dump({"comprobado_utc":now.isoformat()},file)
        os.replace(tmp,path)
    finally:
        if tmp is not None:tmp.unlink(missing_ok=True)
    return True

def run_updates(*, root=None,bundle_root=None, cancel=None,progress=None,
                components=COMPONENTS, force=False, platform=None):
    """Actualiza en segundo plano. Fallos no cambian el componente activo."""
    root=managed_root(root)
    if not force and not load_settings(root)["buscar_al_abrir"]:
        return ["Búsqueda al abrir desactivada"]
    if not force and not update_due(root):
        return ["Actualizaciones comprobadas hace menos de 24 horas"]
    if not force and not load_auto_install(root):
        return ["Búsqueda activada; instalación automática desactivada"]
    results=[]
    for component in components:
        if cancel is not None and cancel.is_set():
            results.append("Actualización cancelada"); break
        try:
            msg=update_component(component,root=root,bundle_root=bundle_root,
                cancel=cancel,progress=progress,platform=platform)
            results.append(msg)
        except Exception as exc:
            # No enviar rutas, tokens, datos o excepciones remotas a la interfaz.
            results.append(component+": se conservó la versión anterior ("+
                (str(exc)[:140] if isinstance(exc,(UpdateSkipped,ValueError,FileExistsError))
                 else "verifica Python, uv, driver o conexión")+")")
    return results
