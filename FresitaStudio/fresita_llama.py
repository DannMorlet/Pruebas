"""Gestor optativo de llama.cpp para Windows x64 y CUDA 13.4.

Sin descargas ni ejecuciones al importar. Los paquetes se obtienen
exclusivamente de los artefactos oficiales de ggml-org/llama.cpp.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import tempfile
from urllib.request import Request, urlopen
import zipfile

from fresita_core import BASE

API = "https://api.github.com/repos/ggml-org/llama.cpp/releases"
RELEASE_ROOT = "https://github.com/ggml-org/llama.cpp/releases/download/"
CUDA_FAMILY = "13.4"
MAX_ZIP_BYTES = 750_000_000
MAX_UNPACKED = 2_000_000_000
USER_AGENT = "FresitaStudio/0.4 (Windows x64; llama.cpp releases)"

def _json_request(url, opener=urlopen):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept":"application/vnd.github+json"})
    with opener(req, timeout=18) as response:
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("Respuesta de GitHub demasiado grande")
    return json.loads(raw)

def select_release(releases):
    """Selecciona la compilación más reciente que INCLUYA ambos ZIP x64 CUDA 13.4."""
    if not isinstance(releases, list):
        raise ValueError("Respuesta de releases inválida")
    for release in releases:
        tag = str(release.get("tag_name", ""))
        if not re.fullmatch(r"b[0-9]+", tag) or release.get("draft"):
            continue
        desired = (
            f"llama-{tag}-bin-win-cuda-13.4-x64.zip",
            "cudart-llama-bin-win-cuda-13.4-x64.zip"
        )
        assets = {asset.get("name"): asset for asset in release.get("assets", [])
                  if isinstance(asset, dict)}
        if not all(name in assets for name in desired):
            continue
        files = []
        for name in desired:
            a = assets[name]
            size = a.get("size", 0)
            digest = a.get("digest", "")
            if not isinstance(size, int) or not 0 < size < MAX_ZIP_BYTES:
                break
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(digest)):
                break
            files.append({"name": name, "size": size, "digest": digest,
                          "url": RELEASE_ROOT + tag + "/" + name})
        if len(files) == 2:
            return {"tag":tag,"cuda": CUDA_FAMILY,"assets":files}
    raise ValueError("No se encontró una versión oficial Windows x64 CUDA 13.4 con firmas SHA-256")

def latest_compatible_release(opener=urlopen):
    return select_release(_json_request(API + "?per_page=15", opener=opener))

def _download_verified(asset, target, opener=urlopen, progress=None):
    if not asset["url"].startswith(RELEASE_ROOT):
        raise ValueError("URL ajena a ggml-org/llama.cpp")
    h = hashlib.sha256()
    transferred = 0
    req = Request(asset["url"], headers={"User-Agent": USER_AGENT})
    with opener(req, timeout=60) as response, Path(target).open("xb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            transferred += len(chunk)
            if transferred > MAX_ZIP_BYTES or transferred > asset["size"]:
                raise ValueError("Descarga excede tamaño publicado")
            out.write(chunk)
            h.update(chunk)
            if progress:
                progress(f"{asset['name']}: {transferred // 1_000_000}/{asset['size'] // 1_000_000} MB")
    if transferred != asset["size"] or h.hexdigest() != asset["digest"].split(":")[1]:
        raise ValueError("Tamaño o SHA-256 del paquete no coincide con GitHub")

def _extract_safe(archive, dest):
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    total = 0
    with zipfile.ZipFile(archive) as z:
        members = z.infolist()
        if len(members) > 10000:
            raise ValueError("ZIP contiene demasiados archivos")
        for item in members:
            name = item.filename.replace("\\", "/")
            segments = PurePosixPath(name).parts
            if (not name or name.startswith("/") or ":" in name or
                    any(p in ("..", "") for p in segments) or
                    (item.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError("Ruta o enlace inseguro en el ZIP")
            total += item.file_size
            if total > MAX_UNPACKED:
                raise ValueError("ZIP excede el límite de extracción")
            output = dest.joinpath(*segments)
            if item.is_dir():
                output.mkdir(parents=True, exist_ok=True)
                continue
            output.parent.mkdir(parents=True, exist_ok=True)
            if output.exists():
                raise ValueError("Archivo duplicado en el ZIP")
            with z.open(item) as src, output.open("xb") as dst:
                shutil.copyfileobj(src, dst)

def _verify_pe64(exe):
    with Path(exe).open("rb") as f:
        if f.read(2) != b"MZ":
            raise ValueError("llama-server.exe no es un ejecutable Windows")
        f.seek(0x3c)
        offset_bytes = f.read(4)
        if len(offset_bytes) != 4:
            raise ValueError("PE incompleto")
        offset = struct.unpack("<I", offset_bytes)[0]
        if offset > 100_000_000:
            raise ValueError("Offset PE inválido")
        f.seek(offset)
        if f.read(4) != b"PE\\x00\\x00".replace(b"\\x00", b"\x00"):
            raise ValueError("Firma PE inválida")
        if struct.unpack("<H", f.read(2))[0] != 0x8664:
            raise ValueError("llama-server no es AMD64")

def install_release(release, root=None, opener=urlopen, progress=None):
    """Descarga 2 ZIPs con SHA256, extrae en staging y publica atómicamente."""
    if os.name != "nt":
        raise OSError("Instalación del motor disponible sólo en Windows x64")
    if not re.fullmatch(r"b[0-9]+", release.get("tag", "")):
        raise ValueError("Etiqueta de release inválida")
    root = Path(root or BASE / "motores" / "llama")
    root.mkdir(parents=True, exist_ok=True)
    target = root / release["tag"]
    if target.exists():
        raise FileExistsError("Esta versión ya existe. No se sobrescribe.")
    with tempfile.TemporaryDirectory(prefix=".fresita-", dir=root) as tmp:
        stage = Path(tmp)
        for index, asset in enumerate(release["assets"]):
            path = stage / f"paquete{index}.zip"
            if progress:
                progress("Descargando " + asset["name"])
            _download_verified(asset, path, opener=opener, progress=progress)
            _extract_safe(path, stage / ("bin" if index == 0 else "runtime"))
        server_files = list((stage / "bin").rglob("llama-server.exe"))
        if len(server_files) != 1:
            raise ValueError("No se encontró exactamente un llama-server.exe")
        server = server_files[0]
        runtime = stage / "runtime"
        for lib in runtime.rglob("*.dll"):
            dst = server.parent / lib.name
            if dst.exists():
                if hashlib.sha256(dst.read_bytes()).digest() != hashlib.sha256(lib.read_bytes()).digest():
                    raise ValueError("Bibliotecas CUDA duplicadas con diferente contenido")
            else:
                shutil.copy2(lib, dst)
        _verify_pe64(server)
        relpath = server.relative_to(stage / "bin")
        manifest = {"tag":release["tag"],"cuda":"13.4",
                    "llama_server":str(relpath).replace("\\","/"),
                    "fuente":"ggml-org/llama.cpp","sha256_assets":[a["digest"] for a in release["assets"]]}
        (stage / "bin" / "fresita_llama_manifest.json").write_text(
            json.dumps(manifest, indent=2),encoding="utf-8")
        # Todas las bibliotecas y el ejecutable quedan en la carpeta versionada.
        (stage / "bin").rename(target)
        return target / relpath

def installed_server(root=None):
    root = Path(root or BASE / "motores" / "llama")
    if not root.is_dir():
        return None
    versions = sorted((p for p in root.iterdir() if re.fullmatch(r"b[0-9]+",p.name)),
                      key=lambda p:int(p.name[1:]),reverse=True)
    for directory in versions:
        manifest_path = directory / "fresita_llama_manifest.json"
        try:
            manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
            rel=PurePosixPath(manifest["llama_server"])
            if not rel.parts or any(part==".." for part in rel.parts):
                continue
            exe=directory.joinpath(*rel.parts)
            if exe.is_file():
                _verify_pe64(exe)
                return exe,manifest["tag"]
        except (OSError,ValueError,KeyError,TypeError):
            continue
    return None

def gpu_compatibility():
    exe=shutil.which("nvidia-smi")
    if not exe:
        return "NVIDIA: controlador no detectado. Verifica el driver antes de iniciar CUDA 13.4."
    try:
        done=subprocess.run([exe,"--query-gpu=name,driver_version,memory.total",
                             "--format=csv,noheader"],capture_output=True,
                             text=True,timeout=5,check=True)
        gpu,driver,mem=[x.strip() for x in done.stdout.splitlines()[0].split(",")[:3]]
        major=int(driver.split(".")[0])
        suffix="R615+ detectado" if major>=615 else "actualiza a controlador compatible R615 para CUDA 13.4"
        return f"{gpu} | driver {driver} | {mem} | {suffix}"
    except (OSError,ValueError,IndexError,subprocess.SubprocessError):
        return "No se pudo comprobar el driver NVIDIA."

def start_server(executable, gguf, port=8080):
    """Sólo bucle local y GGUF elegido explícitamente; nunca shell=True."""
    exe=Path(executable).resolve(strict=True)
    model=Path(gguf).expanduser().resolve(strict=True)
    _verify_pe64(exe)
    if not model.is_file() or model.suffix.lower() != ".gguf":
        raise ValueError("Selecciona un archivo GGUF existente")
    if not 1024<=int(port)<=65535:
        raise ValueError("Puerto inválido")
    log=exe.parent / "fresita_server.log"
    handle=log.open("ab")
    try:
        args=[str(exe),"--model",str(model),"--host","127.0.0.1",
              "--port",str(port),"--ctx-size","2048","--gpu-layers","20"]
        proc=subprocess.Popen(args,cwd=str(exe.parent),stdin=subprocess.DEVNULL,
            stdout=handle,stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    finally:
        handle.close()
    return proc
