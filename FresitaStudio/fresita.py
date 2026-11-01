"""Fresita Studio: panel Windows x64 en español mexicano, sin ML requerido para abrir."""
from __future__ import annotations
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from urllib.request import urlopen

from fresita_core import BASE, init_workspace, import_dataset, clean_dataset, audit_dataset, split_dataset, inspect_safetensors, save_recipe, gpu_summary

BG="#110F18"; PANEL="#221D2B"; PINK="#F57CAD"; TEXT="#FFF4FB"; MUTED="#B8ABBF"
FONT="Segoe UI"

class Fresita(tk.Tk):
    def __init__(self):
        super().__init__()
        init_workspace()
        self.title("🍓 Fresita Studio | IA en español")
        self.geometry("1120x730")
        self.minsize(870,580)
        self.configure(bg=BG)
        self.events=queue.Queue()
        self.proc=None
        self.logs=[]
        self.dataset_path=tk.StringVar()
        self.model=tk.StringVar(value="Qwen/Qwen3-0.6B")
        self.mode=tk.StringVar(value="LoRA")
        self.steps=tk.StringVar(value="100")
        self.lr=tk.StringVar(value="0.0001")
        self.rank=tk.StringVar(value="8")
        self.endpoint=tk.StringVar(value="http://127.0.0.1:1234/v1")
        self.gpu=tk.StringVar(value="GPU: no consultada")
        self.shell()
        self.show("Inicio")
        self.after(150,self.pump)
        self.after(200,self.scan_gpu)
        self.protocol("WM_DELETE_WINDOW",self.close)

    def label(self,parent,value,size=11,color=TEXT,bold=False):
        w=tk.Label(parent,text=value,bg=parent.cget("bg"),fg=color,
                   font=(FONT,size,"bold" if bold else "normal"),
                   justify="left",anchor="w",wraplength=720)
        w.pack(anchor="w",pady=5)
        return w

    def button(self,parent,value,fn,accent=False):
        b=tk.Button(parent,text=value,command=fn,relief="flat",
                    fg=BG if accent else TEXT,bg=PINK if accent else "#393042",
                    activebackground="#D65591",activeforeground=TEXT,
                    cursor="hand2",font=(FONT,10,"bold"),padx=17,pady=10)
        b.pack(anchor="w",pady=5)
        return b

    def field(self,parent,title,var):
        self.label(parent,title,10,MUTED,True)
        x=tk.Entry(parent,textvariable=var,bg="#312A3A",fg=TEXT,insertbackground=PINK,
                   font=(FONT,11),relief="flat")
        x.pack(fill="x",ipady=9,pady=(0,8))
        return x

    def shell(self):
        sidebar=tk.Frame(self,bg="#19151F",width=215)
        sidebar.pack(side="left",fill="y");sidebar.pack_propagate(False)
        self.label(sidebar,"   🍓 FRESITA",20,PINK,True)
        self.label(sidebar,"      AI TRAINING STUDIO",9,MUTED,True)
        for name in ("Inicio","Modelos","Datasets","Entrenar","Crear IA","Actividad"):
            self.button(sidebar,"  "+name,lambda n=name:self.show(n))
        self.label(sidebar,"   Local · Windows x64",9,MUTED)
        main=tk.Frame(self,bg=BG)
        main.pack(side="left",fill="both",expand=True)
        bar=tk.Frame(main,bg=BG)
        bar.pack(fill="x",padx=25,pady=10)
        tk.Label(bar,textvariable=self.gpu,bg=PANEL,fg="#B2E5C1",
                 font=(FONT,9),padx=13,pady=9).pack(side="right")
        self.page=tk.Frame(main,bg=BG)
        self.page.pack(fill="both",expand=True,padx=28,pady=10)
        self.status=tk.StringVar(value="Lista · Los modelos se ejecutan sólo cuando los solicitas")
        tk.Label(main,textvariable=self.status,bg="#19151F",fg=MUTED,
                 anchor="w",padx=25,pady=7,font=(FONT,9)).pack(side="bottom",fill="x")

    def clear(self):
        for w in self.page.winfo_children():w.destroy()

    def card(self):
        c=tk.Frame(self.page,bg=PANEL,padx=20,pady=16)
        c.pack(fill="x",pady=8)
        return c

    def show(self,name):
        self.clear()
        self.label(self.page,name,25,TEXT,True)
        if name=="Inicio":
            c=self.card()
            self.label(c,"Crea. Edita. Entrena. Evalúa.",20,PINK,True)
            self.label(c,"Fresita organiza proyectos y entrenamiento local sin exigir servicios de pago.",11)
            self.label(c,"LoRA y QLoRA usan modelos existentes; crear redes desde cero requiere entrenamiento posterior.",10,MUTED)
            self.button(c,"Preparar mi primera IA",lambda:self.show("Crear IA"),True)
            self.button(c,"Entrenar Qwen3-0.6B",lambda:self.show("Entrenar"))
        elif name=="Datasets":
            c=self.card()
            self.label(c,"Importación y limpieza de datos",16,PINK,True)
            self.field(c,"RUTA ACTUAL",self.dataset_path)
            self.button(c,"Importar JSON / JSONL / CSV / TXT",self.pick_dataset,True)
            self.button(c,"Eliminar duplicados en una copia",self.dedup)
            self.button(c,"Auditar calidad del dataset",self.audit)
            self.button(c,"Separar 90% entrenamiento / 10% validación",self.split)
            self.label(c,"Se guardan copias en Documentos/Fresita Studio/datasets. La separación no evalúa por sí sola el modelo.",10,MUTED)
        elif name=="Modelos":
            c=self.card()
            self.label(c,"Inspección segura de modelos",16,PINK,True)
            self.button(c,"Inspeccionar carpeta Safetensors",self.inspect,True)
            self.label(c,"Cuenta los elementos de tensores sin cargar los pesos en GPU.",10,MUTED)
        elif name=="Crear IA":
            c=self.card()
            self.label(c,"Crear proyecto de IA",16,PINK,True)
            self.field(c,"MODELO O ARQUITECTURA DE PARTIDA",self.model)
            self.button(c,"Guardar receta de creación",self.save_project,True)
            self.label(c,"Esto guarda una receta, no inventa pesos entrenados.",10,MUTED)
        elif name=="Entrenar":
            c=self.card()
            self.label(c,"Entrenamiento con GPU NVIDIA",16,PINK,True)
            self.field(c,"MODELO BASE: ID HUGGING FACE O CARPETA",self.model)
            self.label(c,"MÉTODO",10,MUTED,True)
            ttk.Combobox(c,textvariable=self.mode,values=["LoRA","QLoRA (4-bit)"],state="readonly").pack(fill="x")
            self.field(c,"DATASET JSONL CON COLUMNA TEXT",self.dataset_path)
            self.field(c,"PASOS",self.steps)
            self.field(c,"RANGO LoRA",self.rank)
            self.field(c,"TASA DE APRENDIZAJE",self.lr)
            self.button(c,"Iniciar entrenamiento real",self.train,True)
            self.button(c,"Detener proceso",self.stop)
            self.label(c,"Requiere entorno Python con PyTorch CUDA, Transformers, PEFT, TRL, datasets y opcional bitsandbytes.",9,MUTED)
        elif name=="Actividad":
            c=self.card()
            self.button(c,"Detener entrenamiento",self.stop)
            self.console=tk.Text(c,bg="#15121E",fg="#AFE6C0",height=20,
                    font=("Consolas",10),relief="flat")
            self.console.pack(fill="both",expand=True)
            self.console.insert("1.0","\n".join(self.logs[-400:]))
            self.console.configure(state="disabled")

    def pick_dataset(self):
        filename=filedialog.askopenfilename(filetypes=[("Datos","*.jsonl *.json *.csv *.txt")])
        if not filename:return
        try:
            path,n=import_dataset(Path(filename))
            self.dataset_path.set(str(path))
            messagebox.showinfo("Datos importados",f"{n} ejemplos válidos\n{path}")
        except (OSError,ValueError,UnicodeError) as e:messagebox.showerror("Error",str(e))

    def dedup(self):
        try:
            result,n=clean_dataset(Path(self.dataset_path.get()))
            self.dataset_path.set(str(result))
            messagebox.showinfo("Limpieza",f"{n} ejemplos únicos\n{result}")
        except (OSError,ValueError) as e:messagebox.showerror("Error",str(e))


    def audit(self):
        try:
            s=audit_dataset(Path(self.dataset_path.get()))
            messagebox.showinfo("Auditoría de datos",
                f"Ejemplos válidos: {s['validos']}\\n"
                f"Únicos: {s['unicos']}\\n"
                f"Duplicados: {s['duplicados']}\\n"
                f"Inválidos: {s['invalidos']}\\n"
                f"Longitud promedio: {s['caracteres_promedio']} caracteres\\n"
                "No se han enviado datos a internet.")
        except (OSError,ValueError,UnicodeError) as e:
            messagebox.showerror("No se pudo auditar",str(e))

    def split(self):
        try:
            train,val,nt,nv=split_dataset(Path(self.dataset_path.get()))
            self.dataset_path.set(str(train))
            messagebox.showinfo("Datos separados",
                f"Entrenamiento: {nt} ejemplos\\n{train}\\n\\n"
                f"Validación: {nv} ejemplos\\n{val}\\n\\n"
                "Se seleccionó el archivo de entrenamiento. Guarda el de validación para medir calidad posteriormente.")
        except (OSError,ValueError,UnicodeError) as e:
            messagebox.showerror("No se pudo separar",str(e))

    def inspect(self):
        filename=filedialog.askdirectory(title="Selecciona carpeta de un modelo")
        if not filename:return
        try:
            count,files=inspect_safetensors(Path(filename))
            messagebox.showinfo("Modelo inspeccionado",f"{files} archivos de pesos\n{count:,} valores almacenados")
        except (OSError,ValueError) as e:messagebox.showerror("Error",str(e))

    def save_project(self):
        try:
            path=save_recipe({"tipo":"creacion","modelo_base":self.model.get(),
                              "nota":"Receta; no contiene pesos"})
            messagebox.showinfo("Proyecto guardado",str(path))
        except (OSError,ValueError) as e:messagebox.showerror("Error",str(e))

    def train(self):
        if self.proc and self.proc.poll() is None:
            messagebox.showwarning("Ocupado","Ya hay un trabajo ejecutándose");return
        try:
            steps=int(self.steps.get());rank=int(self.rank.get());lr=float(self.lr.get())
            data=Path(self.dataset_path.get())
            if not (1<=steps<=10000 and 1<=rank<=128 and 1e-7<=lr<=0.01 and data.is_file()):
                raise ValueError("Revisa pasos (1-10000), rango (1-128), LR y ruta al dataset")
            stats=audit_dataset(data)
            if stats["unicos"]<2 or stats["invalidos"]:
                raise ValueError("El dataset debe tener al menos 2 ejemplos únicos y ninguna fila inválida. Audita y limpia los datos.")
            cfg={"model":self.model.get().strip(),"dataset":str(data.resolve()),
                 "steps":steps,"rank":rank,"lr":lr,"qlora":self.mode.get().startswith("QLoRA"),
                 "output":str(BASE/"experiments"/("job-"+time.strftime("%Y%m%d-%H%M%S")))}
            if not cfg["model"]:raise ValueError("Introduce el modelo base")
            recipe=save_recipe(cfg)
            python=(BASE/".venv"/"Scripts"/"python.exe")
            if not python.exists():raise ValueError("Instala el entorno de entrenamiento .venv con Python x64")
            script=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parent))/"workers"/"train_lora.py"
            if not script.exists():raise FileNotFoundError("Falta workers/train_lora.py")
            if not messagebox.askyesno("Entrenar IA","¿Iniciar entrenamiento real con la GPU? Se pueden descargar pesos grandes."):return
            flags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0
            self.proc=subprocess.Popen([str(python),str(script),"--config",str(recipe)],
                  stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
                  text=True,encoding="utf-8",errors="replace",creationflags=flags)
            self.status.set("Entrenamiento activo")
            threading.Thread(target=self.read_logs,args=(self.proc,),daemon=True).start()
        except (OSError,ValueError) as e:messagebox.showerror("No se inició",str(e))

    def read_logs(self,proc):
        for line in proc.stdout:self.events.put(("log",line.rstrip()))
        self.events.put(("done",proc.wait()))

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.status.set("Detención solicitada")
        else:self.status.set("Sin entrenamiento activo")

    def scan_gpu(self):
        threading.Thread(target=lambda:self.events.put(("gpu",gpu_summary())),daemon=True).start()

    def pump(self):
        try:
            while True:
                kind,data=self.events.get_nowait()
                if kind=="gpu":self.gpu.set(data)
                if kind=="log":
                    self.logs.append(data)
                    if hasattr(self,"console") and self.console.winfo_exists():
                        self.console.configure(state="normal")
                        self.console.insert("end",data+"\n")
                        self.console.see("end");self.console.configure(state="disabled")
                if kind=="done":self.status.set("Terminado (código "+str(data)+")")
        except queue.Empty:pass
        self.after(150,self.pump)

    def close(self):
        if self.proc and self.proc.poll() is None:
            if not messagebox.askyesno("Entrenamiento activo","¿Detener el proceso y salir?"):return
            self.proc.terminate()
        self.destroy()

if __name__=="__main__":
    Fresita().mainloop()
