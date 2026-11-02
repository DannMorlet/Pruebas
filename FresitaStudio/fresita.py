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

from fresita_core import BASE, init_workspace, import_dataset, clean_dataset, audit_dataset, split_dataset, validate_eval_pair, inspect_safetensors, save_recipe, gpu_summary
from fresita_metrics import list_experiments,read_history,read_summary,compare_summaries
from fresita_quality import evaluate_predictions, save_quality_report
from fresita_predict import generate_predictions, read_cases, local_server
from fresita_speed import benchmark_local
from fresita_pid import discover_server_pid
from fresita_process_tree import discover_possible_children

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
        self.experiment_items=[]
        self.selected_history=[]
        self.compare_histories=None
        self.dataset_path=tk.StringVar()
        self.validation_path=tk.StringVar()
        self.model=tk.StringVar(value="Qwen/Qwen3-0.6B")
        self.mode=tk.StringVar(value="LoRA")
        self.steps=tk.StringVar(value="100")
        self.lr=tk.StringVar(value="0.0001")
        self.rank=tk.StringVar(value="8")
        self.endpoint=tk.StringVar(value="http://127.0.0.1:1234/v1")
        self.benchmark_path=tk.StringVar()
        self.server_pid=tk.StringVar()
        self.benchmark_cancel=threading.Event()
        self.benchmark_running=False
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
        for name in ("Inicio","Modelos","Datasets","Entrenar","Crear IA","Experimentos","Evaluar IA","Actividad"):
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
            self.field(c,"VALIDACIÓN JSONL (OPCIONAL, NO SE ENTRENA CON ÉL)",self.validation_path)
            self.button(c,"Seleccionar archivo de validación",self.choose_validation)
            self.field(c,"PASOS",self.steps)
            self.field(c,"RANGO LoRA",self.rank)
            self.field(c,"TASA DE APRENDIZAJE",self.lr)
            self.button(c,"Iniciar entrenamiento real",self.train,True)
            self.button(c,"Detener proceso",self.stop)
            self.label(c,"Con validación independiente, se calcula eval_loss y perplejidad al terminar; no se entrena con el archivo de validación.",9,MUTED)
            self.label(c,"Requiere Python, PyTorch CUDA, Transformers, PEFT, TRL, datasets y opcional bitsandbytes.",9,MUTED)
        elif name=="Experimentos":
            c=self.card()
            self.label(c,"Pérdida real de entrenamiento y validación",16,PINK,True)
            self.label(c,"Métricas locales; no se muestran textos de datasets.",10,MUTED)
            self.button(c,"Actualizar experimentos",self.refresh_experiments,True)
            self.label(c,"Selecciona dos experimentos con clic para comparar; el gráfico individual se mantiene disponible.",9,MUTED)
            self.experiment_list=tk.Listbox(c,height=4,selectmode="multiple",bg="#312A3A",fg=TEXT,
                    selectbackground=PINK,selectforeground=BG,relief="flat",
                    font=(FONT,10),exportselection=False)
            self.experiment_list.pack(fill="x",pady=5)
            self.experiment_list.bind("<<ListboxSelect>>",lambda _event:self.select_experiment())
            self.button(c,"Comparar dos experimentos",self.compare_experiments)
            self.comparison_summary=tk.StringVar(value="Selecciona dos experimentos para comparar eval_loss.")
            tk.Label(c,textvariable=self.comparison_summary,bg=PANEL,fg="#8BD6E3",
                     font=(FONT,10),anchor="w",justify="left",wraplength=720).pack(fill="x",pady=5)
            self.experiment_summary=tk.StringVar(value="Selecciona un experimento.")
            tk.Label(c,textvariable=self.experiment_summary,bg=PANEL,fg=MUTED,
                     font=(FONT,10),anchor="w",justify="left").pack(fill="x",pady=5)
            self.metric_canvas=tk.Canvas(c,bg="#15121E",height=240,highlightthickness=0)
            self.metric_canvas.pack(fill="both",expand=True,pady=6)
            self.metric_canvas.bind("<Configure>",lambda _event:self.draw_experiment_chart())
            self.refresh_experiments()
        elif name=="Evaluar IA":
            c=self.card()
            self.label(c,"Calidad de respuestas · Español MX y Python",16,PINK,True)
            self.label(c,"Evalúa archivos existentes o genera respuestas usando un servidor local.",10,MUTED)
            self.field(c,"SERVIDOR LOCAL (SÓLO 127.0.0.1)",self.endpoint)
            self.field(c,"MODELO CARGADO EN SERVIDOR LOCAL",self.model)
            self.field(c,"PID DEL SERVIDOR (OPCIONAL; VRAM Y RAM POR PROCESO)",self.server_pid)
            self.button(c,"Detectar PID y posibles procesos secundarios",self.detect_pid)
            self.field(c,"BENCHMARK JSONL (PREGUNTA, REFERENCIA, CATEGORIA)",self.benchmark_path)
            self.button(c,"Elegir benchmark",self.choose_benchmark)
            self.button(c,"Generar, medir velocidad y evaluar (local)",self.start_benchmark,True)
            self.button(c,"Cancelar generación",self.cancel_benchmark)
            self.label(c,"Mide latencia, tokens/s, VRAM GPU 0 y RAM global. PID opcional: VRAM del proceso si NVIDIA la informa y RAM física del proceso si Windows permite consultarla.",9,MUTED)
            self.label(c,"Se envía únicamente la pregunta a 127.0.0.1. El JSONL de salida contiene respuestas y referencias privadas; no lo subas a GitHub.",9,MUTED)
            self.button(c,"Evaluar predicciones JSONL",self.evaluate_quality,True)
            self.label(c,"Español: coincidencia normalizada y F1 de tokens. Python: coincidencia y sintaxis; no corrección funcional.",10,MUTED)
            self.label(c,"Se guardan únicamente métricas agregadas y SHA-256. Límite: 8 MB y 5,000 filas.",10,MUTED)
        elif name=="Actividad":
            c=self.card()
            self.button(c,"Detener entrenamiento",self.stop)
            self.console=tk.Text(c,bg="#15121E",fg="#AFE6C0",height=20,
                    font=("Consolas",10),relief="flat")
            self.console.pack(fill="both",expand=True)
            self.console.insert("1.0","\n".join(self.logs[-400:]))
            self.console.configure(state="disabled")

    def refresh_experiments(self):
        try:
            self.experiment_items=list_experiments(BASE/"experiments")
            self.experiment_list.delete(0,"end")
            for folder in self.experiment_items:
                self.experiment_list.insert("end",folder.name)
            self.selected_history=[]
            self.compare_histories=None
            self.comparison_summary.set("Selecciona dos experimentos para comparar eval_loss.")
            if self.experiment_items:
                self.experiment_list.selection_set(0)
                self.select_experiment()
            else:
                self.experiment_summary.set("Todavía no hay entrenamientos con métricas.")
                self.draw_experiment_chart()
        except (OSError,ValueError) as e:
            messagebox.showerror("Experimentos",str(e))

    def select_experiment(self):
        selection=self.experiment_list.curselection()
        if not selection:return
        self.compare_histories=None
        self.comparison_summary.set("Selecciona dos experimentos para comparar eval_loss.")
        folder=self.experiment_items[selection[-1]]
        try:
            self.selected_history=read_history(folder/"metricas_historial.jsonl")
            report=read_summary(folder)
            loss=report.get("eval_loss")
            perplexity=report.get("perplejidad")
            info=f"{folder.name} | {len(self.selected_history)} eventos"
            if loss is not None:info+=f" | eval_loss: {loss:.4f}"
            else:info+=" | Sin evaluación final"
            if perplexity is not None:info+=f" | Perplejidad: {perplexity:.3f}"
            self.experiment_summary.set(info)
            self.draw_experiment_chart()
        except (OSError,ValueError) as e:
            self.experiment_summary.set("No se pudo leer: "+str(e))
            self.selected_history=[]
            self.draw_experiment_chart()

    def compare_experiments(self):
        selection=self.experiment_list.curselection()
        if len(selection)!=2:
            self.comparison_summary.set("Selecciona exactamente dos experimentos con clic.")
            return
        first,second=(self.experiment_items[i] for i in selection)
        try:
            result=compare_summaries(read_summary(first),read_summary(second))
            if not result["comparable"]:
                self.compare_histories=None
                self.comparison_summary.set("No comparables: "+result["motivo"]+
                    ". Los entrenamientos anteriores pueden carecer de huellas; no se inventa un ganador.")
            else:
                winner=result["mejor"]
                who=("Empate" if winner=="empate" else
                     ("Mejor eval_loss: "+(first.name if winner=="A" else second.name)))
                self.comparison_summary.set(
                    f"A: {first.name} ({result['loss_a']:.4f}) | B: {second.name} ({result['loss_b']:.4f})"
                    f" | Δ(B-A): {result['delta_b_menos_a']:+.4f} | {who}. "
                    "Mismo dataset y tokenizador; menor pérdida no garantiza mejores respuestas.")
                self.compare_histories=[
                    (first.name,read_history(first/"metricas_historial.jsonl")),
                    (second.name,read_history(second/"metricas_historial.jsonl"))]
            self.draw_experiment_chart()
        except (OSError,ValueError) as e:
            self.compare_histories=None
            self.comparison_summary.set("Error de comparación: "+str(e))

    def draw_experiment_chart(self):
        canvas=getattr(self,"metric_canvas",None)
        if canvas is None or not canvas.winfo_exists():return
        canvas.delete("all")
        width=max(canvas.winfo_width(),360);height=max(canvas.winfo_height(),200)
        left,right,top,bottom=58,width-18,30,height-35
        canvas.create_line(left,top,left,bottom,fill="#807389")
        canvas.create_line(left,bottom,right,bottom,fill="#807389")
        if self.compare_histories is not None:
            series=[(name[:20]+" eval","#F57CAD" if i==0 else "#8BD6E3",
                [(x["paso"],x["eval_loss"]) for x in history if "eval_loss" in x])
                for i,(name,history) in enumerate(self.compare_histories)]
        else:
            series=[
                ("loss","#F57CAD",[(x["paso"],x["loss"]) for x in self.selected_history if "loss" in x]),
                ("eval_loss","#8BD6E3",[(x["paso"],x["eval_loss"]) for x in self.selected_history if "eval_loss" in x])]
        values=[v for _,_,points in series for _,v in points]
        steps=[s for _,_,points in series for s,_ in points]
        if not values:
            canvas.create_text(width//2,height//2,text="Sin métricas registradas",fill=MUTED,font=(FONT,12))
            return
        ymin,ymax=min(values),max(values)
        if ymin==ymax:ymin-=0.5;ymax+=0.5
        xmin,xmax=min(steps),max(steps)
        if xmin==xmax:xmax+=1
        for i in range(5):
            y=top+(bottom-top)*i/4
            v=ymax-(ymax-ymin)*i/4
            canvas.create_line(left,y,right,y,fill="#332B3B",dash=(2,5))
            canvas.create_text(left-6,y,text=f"{v:.3g}",fill=MUTED,anchor="e",font=(FONT,9))
        for index,(label,color,points) in enumerate(series):
            canvas.create_text(left+(190*index),12,
                text=label,fill=color,anchor="w",font=(FONT,10,"bold"))
            coords=[]
            for step,value in points:
                coords.extend((left+(right-left)*(step-xmin)/(xmax-xmin),
                               bottom-(bottom-top)*(value-ymin)/(ymax-ymin)))
            if len(coords)>=4:canvas.create_line(*coords,fill=color,width=2)
            elif len(coords)==2:
                x,y=coords
                canvas.create_oval(x-3,y-3,x+3,y+3,fill=color,outline="")
        canvas.create_text(left,bottom+17,text=str(xmin),fill=MUTED,anchor="w",font=(FONT,9))
        canvas.create_text(right,bottom+17,text=f"Paso {xmax}",fill=MUTED,anchor="e",font=(FONT,9))

    def choose_benchmark(self):
        filename=filedialog.askopenfilename(title="Benchmark de preguntas",filetypes=[("JSONL","*.jsonl")])
        if filename:self.benchmark_path.set(filename)

    def detect_pid(self):
        """Identifica el listener en segundo plano, sin bloquear la interfaz."""
        endpoint = self.endpoint.get().strip()
        try:
            local_server(endpoint)
        except ValueError as exc:
            messagebox.showerror("Servidor local", str(exc))
            return
        self.status.set("Buscando proceso que escucha en el puerto local...")
        def worker():
            pid = discover_server_pid(endpoint)
            children = discover_possible_children(pid) if pid is not None else None
            self.events.put(("pid_discovered", (endpoint, pid, children)))
        threading.Thread(target=worker, daemon=True).start()

    def start_benchmark(self):
        if self.benchmark_running:
            messagebox.showwarning("Ocupado","Ya se están generando predicciones.")
            return
        try:
            endpoint=self.endpoint.get().strip()
            model=self.model.get().strip()
            local_server(endpoint)
            if not model or len(model)>256:
                raise ValueError("Especifica el identificador exacto del modelo cargado.")
            dataset=Path(self.benchmark_path.get().strip())
            cases=read_cases(dataset)
            pid_text=self.server_pid.get().strip()
            if pid_text and (not pid_text.isascii() or not pid_text.isdecimal()
                             or not 1 <= int(pid_text) <= 4294967295):
                raise ValueError("PID inválido: usa un entero positivo de Windows.")
            process_pid=int(pid_text) if pid_text else None
            if not messagebox.askyesno("Inferencia local",
                f"Se enviarán {len(cases)} preguntas a {endpoint}.\n"
                "Sólo se enviarán las preguntas, no las referencias.\n"
                "Los resultados privados quedarán en tu equipo. "
                + (f"Se medirá VRAM del PID {process_pid} si está disponible. " if process_pid else "")
                + "¿Continuar?"):
                return
            self.benchmark_cancel.clear()
            self.benchmark_running=True
            self.status.set("Generando predicciones locales: 0/"+str(len(cases)))
            threading.Thread(target=self.run_benchmark,
                args=(dataset,endpoint,model,process_pid),daemon=True).start()
        except (OSError,ValueError,UnicodeError) as e:
            messagebox.showerror("Benchmark no iniciado",str(e))

    def run_benchmark(self,dataset,endpoint,model,process_pid=None):
        try:
            out,speed_path,speed=benchmark_local(dataset,BASE/"experiments"/"predicciones",
                workspace=BASE,endpoint=endpoint,model=model,
                process_pid=process_pid, cancelled=self.benchmark_cancel.is_set,
                progress=lambda i,n:self.events.put(("benchmark_progress",(i,n))))
            report=evaluate_predictions(out)
            saved=save_quality_report(report,BASE)
            self.events.put(("benchmark_done",(str(out),str(saved),speed["muestras"],str(speed_path),speed)))
        except Exception as e:
            self.events.put(("benchmark_error",str(e)))

    def cancel_benchmark(self):
        if self.benchmark_running:
            self.benchmark_cancel.set()
            self.status.set("Cancelando tras la solicitud local en curso...")
        else:
            self.status.set("No hay predicciones en curso.")

    def evaluate_quality(self):
        filename=filedialog.askopenfilename(title="Predicciones para evaluar",filetypes=[("JSONL","*.jsonl")])
        if not filename:return
        try:
            report=evaluate_predictions(Path(filename))
            output=save_quality_report(report,BASE)
            es=report["metricas"]["es_mx"]
            code=report["metricas"]["codigo_python"]
            def pct(value):
                return "N/D" if value is None else f"{value*100:.1f}%"
            messagebox.showinfo("Evaluación offline terminada",
                f"Ejemplos: {report['ejemplos_validos']} | Filas inválidas: {report['filas_invalidas']}\n"
                f"Español MX ({es['ejemplos']}): exactitud {pct(es['exactitud_normalizada'])}, F1 {pct(es['f1_tokens_promedio'])}\n"
                f"Python ({code['ejemplos']}): exactitud {pct(code['coincidencia_exacta'])}, sintaxis {pct(code['sintaxis_valida'])}\n\n"
                f"Reporte: {output}\nNo se ejecutó código ni se verificó su corrección funcional.")
            self.status.set("Evaluación offline terminada: "+str(report["ejemplos_validos"])+" ejemplos")
        except (OSError,ValueError,UnicodeError) as e:
            messagebox.showerror("Evaluación fallida",str(e))

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
                f"Ejemplos válidos: {s['validos']}\n"
                f"Únicos: {s['unicos']}\n"
                f"Duplicados: {s['duplicados']}\n"
                f"Inválidos: {s['invalidos']}\n"
                f"Longitud promedio: {s['caracteres_promedio']} caracteres\n"
                "No se han enviado datos a internet.")
        except (OSError,ValueError,UnicodeError) as e:
            messagebox.showerror("No se pudo auditar",str(e))

    def split(self):
        try:
            train,val,nt,nv=split_dataset(Path(self.dataset_path.get()))
            self.dataset_path.set(str(train))
            self.validation_path.set(str(val))
            messagebox.showinfo("Datos separados",
                f"Entrenamiento: {nt} ejemplos\n{train}\n\n"
                f"Validación: {nv} ejemplos\n{val}\n\n"
                "Se seleccionó el archivo de entrenamiento. Guarda el de validación para medir calidad posteriormente.")
        except (OSError,ValueError,UnicodeError) as e:
            messagebox.showerror("No se pudo separar",str(e))

    def choose_validation(self):
        filename=filedialog.askopenfilename(filetypes=[("JSONL","*.jsonl")])
        if filename:self.validation_path.set(filename)

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
            if self.validation_path.get().strip():
                val=Path(self.validation_path.get().strip())
                counts=validate_eval_pair(data,val)
                cfg["eval_dataset"]=str(val.resolve())
                cfg["validation_count"]=counts["validacion_unicos"]
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
                if kind=="pid_discovered":
                    endpoint, pid, children = data
                    if endpoint != self.endpoint.get().strip():
                        self.status.set("Cambió el servidor: se descartó el PID anterior.")
                    elif pid is None:
                        self.status.set("PID no disponible o ambiguo. Puedes escribirlo manualmente.")
                    else:
                        self.server_pid.set(str(pid))
                        info = (" Posibles secundarios: " + ", ".join(map(str, children))
                                if children else (" No se observaron hijos." if children == []
                                                  else " Hijos: N/D."))
                        self.status.set(f"Listener PID {pid}." + info + " No se atribuye RAM/VRAM a los hijos.")
                if kind=="log":
                    self.logs.append(data)
                    if hasattr(self,"console") and self.console.winfo_exists():
                        self.console.configure(state="normal")
                        self.console.insert("end",data+"\n")
                        self.console.see("end");self.console.configure(state="disabled")
                if kind=="done":self.status.set("Terminado (código "+str(data)+")")
                if kind=="benchmark_progress":
                    self.status.set(f"Predicciones locales: {data[0]}/{data[1]}")
                if kind=="benchmark_done":
                    self.benchmark_running=False
                    self.status.set(f"Evaluación local terminada: {data[2]} ejemplos")
                    pid_line = (
                        f"VRAM del proceso PID {data[4]['gpu_proceso_pid']}: "
                        f"pico {data[4]['gpu_proceso_pico_mib'] if data[4]['gpu_proceso_pico_mib'] is not None else 'N/D'} MiB\n"
                        if data[4].get("gpu_proceso_pid") is not None else
                        "Sin PID: no se midió VRAM por proceso.\n")
                    if data[4].get("ram_proceso_pid") is not None:
                        ram_peak = data[4].get("ram_proceso_pico_mib")
                        pid_line += (
                            f"RAM física del proceso PID {data[4]['ram_proceso_pid']}: "
                            f"pico {ram_peak if ram_peak is not None else 'N/D'} MiB\n")
                    messagebox.showinfo("Benchmark terminado",
                        f"Predicciones privadas: {data[0]}\nReporte de calidad: {data[1]}\n"
                        f"Reporte de velocidad: {data[3]}\n"
                        f"Latencia media: {data[4]['latencia_media_s']:.3f} s\n"
                        f"Tokens/s extremo a extremo: {data[4]['tokens_salida_por_s_extremo_a_extremo'] if data[4]['tokens_salida_por_s_extremo_a_extremo'] is not None else 'N/D (sin usage)'}\n"
                        f"VRAM GPU 0 global: base {data[4]['gpu_global_base_mib'] if data[4]['gpu_global_base_mib'] is not None else 'N/D'} MiB"
                        f" | pico {data[4]['gpu_global_pico_mib'] if data[4]['gpu_global_pico_mib'] is not None else 'N/D'} MiB\n"
                        f"RAM global: base {data[4]['ram_global_base_mib'] if data[4]['ram_global_base_mib'] is not None else 'N/D'} MiB"
                        f" | pico {data[4]['ram_global_pico_mib'] if data[4]['ram_global_pico_mib'] is not None else 'N/D'} MiB\n"
                        + pid_line
                        + "VRAM y RAM por PID corresponden al proceso completo, no sólo al modelo.\n"
                        "No se envió la referencia al modelo.")
                if kind=="benchmark_error":
                    self.benchmark_running=False
                    self.status.set("Benchmark cancelado o fallido")
                    messagebox.showerror("Benchmark local",data)
        except queue.Empty:pass
        self.after(150,self.pump)

    def close(self):
        self.benchmark_cancel.set()
        if self.proc and self.proc.poll() is None:
            if not messagebox.askyesno("Entrenamiento activo","¿Detener el proceso y salir?"):return
            self.proc.terminate()
        self.destroy()

if __name__=="__main__":
    Fresita().mainloop()
