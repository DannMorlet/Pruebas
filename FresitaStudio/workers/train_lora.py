"""Entrenamiento PEFT/TRL con CUDA y validación opcional independiente."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys

# En desarrollo y en PyInstaller --add-data, fresita_core está en el directorio padre.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fresita_core import validate_eval_pair, evaluation_summary
from fresita_metrics import append_metrics, evaluation_fingerprints
from fresita_training_diagnostics import run_training_stage

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--config",required=True)
    parser.add_argument("--preflight",action="store_true",help="Revisar CUDA y dependencias sin cargar modelos")
    args=parser.parse_args()
    cfg=json.loads(Path(args.config).read_text(encoding="utf-8"))
    from fresita_train_preflight import inspect_environment
    report=inspect_environment(qlora=bool(cfg.get("qlora")))
    print("DIAGNÓSTICO CUDA:",json.dumps(report,ensure_ascii=False),flush=True)
    if not report["ok"]:
        raise RuntimeError("Entorno de entrenamiento incompleto: "+"; ".join(report["errores"]))
    if args.preflight:
        print("DIAGNÓSTICO COMPLETADO: no se cargaron pesos ni datasets",flush=True)
        return
    import torch
    from datasets import load_dataset
    from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig,TrainerCallback
    from peft import LoraConfig
    from trl import SFTConfig,SFTTrainer
    if not torch.cuda.is_available():
        raise RuntimeError("No se detectó GPU CUDA")
    ds=load_dataset("json",data_files=cfg["dataset"],split="train")
    if "text" not in ds.column_names or len(ds)<2:
        raise ValueError("Mínimo 2 ejemplos text")
    eval_ds=None
    counts=None
    if cfg.get("eval_dataset"):
        counts=validate_eval_pair(cfg["dataset"],cfg["eval_dataset"])
        eval_ds=load_dataset("json",data_files=cfg["eval_dataset"],split="train")
        if "text" not in eval_ds.column_names:
            raise ValueError("Validación sin columna text")
    dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    kwargs={"dtype":dtype,"trust_remote_code":False}
    if cfg.get("qlora"):
        kwargs["quantization_config"]=BitsAndBytesConfig(
            load_in_4bit=True,bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=dtype,bnb_4bit_use_double_quant=True)
        kwargs["device_map"]="auto"
    print("Iniciando entrenamiento CUDA con:",torch.cuda.get_device_name(0),flush=True)
    model=run_training_stage("carga",AutoModelForCausalLM.from_pretrained,cfg["model"],**kwargs)
    model.config.use_cache=False
    tok=AutoTokenizer.from_pretrained(cfg["model"],trust_remote_code=False)
    if tok.pad_token is None:tok.pad_token=tok.eos_token
    rank=int(cfg["rank"])
    peft=LoraConfig(r=rank,lora_alpha=rank*2,task_type="CAUSAL_LM",target_modules="all-linear")
    steps=int(cfg["steps"])
    opts=SFTConfig(output_dir=cfg["output"],max_steps=steps,
       per_device_train_batch_size=1,per_device_eval_batch_size=1,
       gradient_accumulation_steps=4,eval_accumulation_steps=1,
       max_length=256,learning_rate=float(cfg["lr"]),dataset_text_field="text",
       gradient_checkpointing=True,logging_steps=5,save_strategy="no",
       eval_strategy="steps" if eval_ds is not None else "no",
       eval_steps=max(1,steps//5) if eval_ds is not None else None,
       report_to="none",bf16=dtype==torch.bfloat16,fp16=dtype==torch.float16)
    class HistoryCallback(TrainerCallback):
        def on_log(self, args, state, control, logs=None, **kwargs):
            append_metrics(Path(cfg["output"])/"metricas_historial.jsonl",
                           int(state.global_step), logs or {})

    trainer=run_training_stage("preparacion",SFTTrainer,model=model,args=opts,train_dataset=ds,
        eval_dataset=eval_ds,processing_class=tok,peft_config=peft,
        callbacks=[HistoryCallback()])
    run_training_stage("entrenamiento",trainer.train)
    trainer.save_model(cfg["output"])
    tok.save_pretrained(cfg["output"])
    if eval_ds is not None:
        metrics=run_training_stage("evaluacion",trainer.evaluate)
        report=evaluation_summary(metrics,counts["validacion_unicos"],steps)
        report.update(evaluation_fingerprints(cfg["eval_dataset"],tok,256))
        target=Path(cfg["output"])/"metricas_validacion.json"
        tmp=target.with_suffix(".tmp")
        tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),
                       encoding="utf-8")
        os.replace(tmp,target)
        print("VALIDACIÓN FINAL:",json.dumps(report,ensure_ascii=False),flush=True)
        print("MÉTRICAS GUARDADAS EN:",target,flush=True)
        if not report["evaluacion_valida"]:
            raise RuntimeError("La pérdida de validación no es finita: revisa el entrenamiento")
    print("ENTRENAMIENTO COMPLETADO",flush=True)

if __name__=="__main__":
    try:main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
