#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconstruye las 7 IAs Morlet v0.3 desde el ZIP v0.2 que posee el usuario.

No contiene ni redistribuye el motor HD original de terceros.
Uso: python aoe2/build_7_ias.py --base Morlet_AoE2DE_7IAs_Matick_LMStudio_v0_2.zip --out siete_ias
"""
import argparse
from pathlib import Path
import hashlib
import json
import re
import zipfile

NAMES=("Matick","Nemesis","Tyran","Mazapan","Nutella","Gemini","Copilot")
SOURCE=("Agua_de_Morlet.per","Nemesis.per","Agua_de_Mazapan.per",
        "Capuchino_de-Mazapan.per","AI (HD version).per",
        "AI (HD version).per","AI (HD version).per")

ROLES={
"Matick": """
; Matick 1: el motor .per conserva MORLET ADAPTIVE.
; Matick Gemma 4 en LM Studio se conecta mediante un puente externo, no .per.
""",
"Nemesis": """
; Nemesis 2: Qwen3-0.6B en C:\\NPU necesita controlador OpenVINO externo.
(defrule
 (game-time > 1000)
 (military-population >= 18)
=>
 (set-strategic-number sn-percent-attack-soldiers 85)
 (disable-self))
""",
"Tyran": """
; Tyran 3: presion militar y flancos.
; Modelo SmolLM2-360M compartido con Mazapan via servicio externo en GPU.
(defrule
 (game-time > 650)
 (military-population >= 12)
=>
 (set-strategic-number sn-percent-attack-soldiers 80)
 (disable-self))
""",
"Mazapan": """
; Mazapan 4: economia, reconstruccion y prudencia.
; Mismo modelo SmolLM2-360M pero identidad y memoria separadas de Tyran.
(defrule
 (game-time > 280)
 (military-population < 10)
=>
 (set-strategic-number sn-percent-attack-soldiers 45)
 (disable-self))
""",
"Nutella": """
; Nutella 5: Untador expande; Hormiga hostiga; Chocolate Negro desgasta;
; Avellana explota debilidades; Empalagador Supremo reconstruye.
; Sus cinco nombres son subroles logicos, no cinco modelos LLM.
(defrule
 (current-age >= castle-age)
 (civilian-population >= 15)
 (building-type-count town-center < 2)
 (can-build town-center)
=>
 (build town-center)
 (disable-self))
""",
"Gemini": """
; Gemini 6: Tesorero + Explorador, distribucion inicial por edad del PDF.
; Porcentajes pueden ser ajustados posteriormente por el motor HD.
(defrule
 (current-age == dark-age)
 (game-time > 15)
=>
 (set-strategic-number sn-food-gatherer-percentage 55)
 (set-strategic-number sn-wood-gatherer-percentage 35)
 (set-strategic-number sn-gold-gatherer-percentage 10)
 (set-strategic-number sn-stone-gatherer-percentage 0)
 (disable-self))
(defrule
 (current-age == feudal-age)
=>
 (set-strategic-number sn-food-gatherer-percentage 45)
 (set-strategic-number sn-wood-gatherer-percentage 40)
 (set-strategic-number sn-gold-gatherer-percentage 15)
 (set-strategic-number sn-stone-gatherer-percentage 0)
 (disable-self))
(defrule
 (current-age == castle-age)
=>
 (set-strategic-number sn-food-gatherer-percentage 40)
 (set-strategic-number sn-wood-gatherer-percentage 35)
 (set-strategic-number sn-gold-gatherer-percentage 20)
 (set-strategic-number sn-stone-gatherer-percentage 5)
 (disable-self))
(defrule
 (current-age == imperial-age)
=>
 (set-strategic-number sn-food-gatherer-percentage 35)
 (set-strategic-number sn-wood-gatherer-percentage 35)
 (set-strategic-number sn-gold-gatherer-percentage 20)
 (set-strategic-number sn-stone-gatherer-percentage 10)
 (disable-self))
""",
"Copilot": """
; Copilot 7: comandante, economista, explorador, ingeniero, general,
; defensor, analista, logistica, predictivo y cazador de oportunidades.
; No implica servicio comercial ni diez procesos adicionales.
(defrule
 (game-time > 200)
 (current-age >= feudal-age)
=>
 (set-strategic-number sn-total-number-explorers 2)
 (disable-self))
(defrule
 (game-time > 900)
 (military-population >= 20)
=>
 (set-strategic-number sn-percent-attack-soldiers 75)
 (disable-self))
"""
}

def audit(name,data):
    s=data.decode("latin1")
    stripped=re.sub(r';[^\r\n]*',"",s)
    stripped=re.sub(r'"(?:[^"\\]|\\.)*"','""',stripped)
    d=0
    for ch in stripped:
        if ch=="(":d+=1
        elif ch==")":
            d-=1
            if d<0:raise ValueError(name+" tiene cierre adicional")
    if d:raise ValueError(name+" parentesis desbalanceados")
    start=len(re.findall(r'(?m)^\s*#load-if-(?:not-)?defined\b',s))
    end=len(re.findall(r'(?m)^\s*#end-if\b',s))
    if start!=end:raise ValueError(name+" directivas desbalanceadas")
    if re.search(r'\(\s*cc-add-resource\b',stripped,re.I):raise ValueError(name+" tiene trucos de recursos")
    rules=len(re.findall(r'\(\s*defrule\b',stripped,re.I))
    if rules<2000:raise ValueError(name+" carece de reglas base")
    return {"name":name,"rules":rules,"sha256":hashlib.sha256(data).hexdigest(),"no_resource_cheats":True}

def build(base,out):
    out=Path(out)
    dest=out/"IA"
    dest.mkdir(parents=True,exist_ok=True)
    audit_rows=[]
    with zipfile.ZipFile(base) as z:
        for idx,(name,origin) in enumerate(zip(NAMES,SOURCE),1):
            key="IA/"+name+".per"
            b=z.read(key)
            if b"; ===== MORLET 7 IAS" not in b:raise ValueError("No es ZIP base v0.2: "+key)
            suffix=("\r\n; ==== MORLET-PERSONALIDAD v0.3 ====\r\n"+ROLES[name].strip()+"\r\n").encode("latin1")
            updated=b+suffix
            row=audit(name,updated)
            row.update({"number":idx,"origin":origin,"requires_promisory":True})
            audit_rows.append(row)
            (dest/(name+".per")).write_bytes(updated)
            (dest/(name+".ai")).write_bytes(b"")
    if len(audit_rows)!=7 or len(list(dest.iterdir()))!=14:raise RuntimeError("Debe haber 14 archivos")
    (out/"AUDITORIA.json").write_text(json.dumps(audit_rows,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("Listo: exactamente 7 IAs / 14 archivos, sin cc-add-resource.")
    print("OJO: requieren Promisory original y pruebas dentro de AoE2 DE.")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    build(a.base,a.out)

if __name__=="__main__":
    main()
