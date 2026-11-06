#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preparar 7 dependencias aisladas Morlet7_*_Core desde el Promisory local.

NO cambia ni sobreescribe la carpeta Promisory original.
NO permite instalar los .per nuevos si no están disponibles las dependencias.
Este script se entrega también en el ZIP v0.4 como IA/preparar_nucleos.py.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import shutil
import tempfile

NAMES = ("Matick", "Nemesis", "Tyran", "Mazapan", "Nutella", "Gemini", "Copilot")
REQUIRED = ("defaultconstants.per", "finalingconstants.per", "finaling.per")

def prepare(source: Path, dest: Path) -> dict:
    source, dest = source.resolve(), dest.resolve()
    if not source.is_dir() or source.name.lower() != "promisory":
        raise ValueError("El origen tiene que ser una carpeta existente Promisory")
    if source == dest or source in dest.parents or dest in source.parents:
        raise ValueError("El destino y origen no deben contenerse entre sí")
    found = {x.name.lower() for x in source.iterdir() if x.is_file()}
    missing = [r for r in REQUIRED if r not in found]
    if missing:
        raise ValueError("Faltan dependencias: " + ", ".join(missing))
    files = list(source.rglob("*"))
    if any(p.is_symlink() for p in files):
        raise ValueError("No se aceptan enlaces simbólicos")
    sources = [p for p in files if p.is_file()]
    if len(sources) > 3000 or sum(p.stat().st_size for p in sources) > 300_000_000:
        raise ValueError("Origen anómalo; comprobar que la carpeta es la correcta")
    for name in NAMES:
        target = dest / ("Morlet7_" + name + "_Core")
        if target.exists():
            raise FileExistsError(f"No sobrescribo {target}")
        per = dest / (name + ".per")
        if not per.exists() or ("Morlet7_" + name + "_Core").encode() not in per.read_bytes():
            raise ValueError(f"Falta el .per v0.4 aislado de {name}")
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="morlet7_", dir=dest) as t:
        temp = Path(t)
        prepared = []
        for name in NAMES:
            folder = temp / ("Morlet7_" + name + "_Core")
            shutil.copytree(source, folder)
            for p in folder.rglob("*"):
                if p.is_file() and p.suffix.lower() in (".per", ".per2"):
                    old = p.read_bytes()
                    new = re.sub(
                        rb"(?i)Promisory([\\/])",
                        lambda m: ("Morlet7_" + name + "_Core").encode("ascii") + m.group(1),
                        old,
                    )
                    if new != old:
                        p.write_bytes(new)
            prepared.append(folder)
        for folder in prepared:
            folder.rename(dest / folder.name)
    return {"carpetas_creadas": len(NAMES),
            "archivos_por_carpeta": len(sources),
            "promisory_original_modificado": False}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fuente", required=True, type=Path)
    p.add_argument("--destino", required=True, type=Path)
    args = p.parse_args()
    try:
        print(prepare(args.fuente, args.destino))
    except (ValueError, OSError) as exc:
        print("ERROR: no instales los nuevos .per hasta corregir esto:", exc)
        raise SystemExit(2)
