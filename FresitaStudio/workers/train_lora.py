"""Entrenamiento PEFT/TRL con CUDA y validación opcional independiente."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
from importlib import metadata

# En desarrollo y en PyInstaller --add-data, fresita_core está en el directorio padre.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fresita_core import validate_eval_pair, evaluation_summary
from fresita_metrics import append_metrics, evaluation_fingerprints
from fresita_training_diagnostics import run_training_stage
from fresita_checkpoints import sft_training_kwargs
from fresita_resume import prepare_training_run, installed_runtime_versions

def validate_backend(cfg):
    """Elegir backend sin efectos secundarios; Unsloth no reanuda checkpoints aún."""
    backend = cfg.get("backend", "trl")
    if backend not in ("trl", "unsloth"):
        raise ValueError("Backend de entrenamiento no reconocido.")
    if backend == "unsloth" and (
        cfg.get("checkpoint_interval", 0) or cfg.get("resume_checkpoint")
    ):
        raise ValueError(
            "Los checkpoints y la reanudación de Unsloth no están validados. "
            "Desactívalos o usa TRL/PEFT."
        )
    return backend


def load_unsloth_model(model_id, rank, qlora, fast_language_model):
    """Carga modelo y prepara LoRA con la API oficial de Unsloth.

    Se inyecta FastLanguageModel para probar los argumentos sin CUDA en CI.
    """
    if not isinstance(model_id, str) or not model_id.strip():
        raise ValueError("Indica un modelo base válido.")
    if type(rank) is not int or not 1 <= rank <= 128:
        raise ValueError("El rango LoRA debe estar entre 1 y 128.")
    if type(qlora) is not bool:
        raise ValueError("QLoRA debe ser booleano.")
    model, tokenizer = fast_language_model.from_pretrained(
        model_name=model_id, max_seq_length=256, dtype=None,
        load_in_4bit=qlora,
    )
    model = fast_language_model.get_peft_model(
        model, r=rank, lora_alpha=rank * 2, lora_dropout=0,
        bias="none",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        use_gradient_checkpointing="unsloth", random_state=3407,
    )
    return model, tokenizer


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--config",required=True)
    parser.add_argument("--preflight",action="store_true",help="Revisar CUDA y dependencias sin cargar modelos")
    args=parser.parse_args()
    cfg=json.loads(Path(args.config).read_text(encoding="utf-8"))
    backend=validate_backend(cfg)
    # Unsloth debe importarse antes de torch/transformers/TRL para aplicar sus parches.
    # En --preflight no se importa Unsloth ni se cargan pesos.
    if backend == "unsloth" and not args.preflight:
        from unsloth import FastLanguageModel
    else:
        FastLanguageModel = None
    from fresita_train_preflight import inspect_environment
    report=inspect_environment(qlora=bool(cfg.get("qlora")))
    if backend == "unsloth":
        try:
            report["dependencias"]["unsloth"] = metadata.version("unsloth")
        except metadata.PackageNotFoundError:
            report["dependencias"]["unsloth"] = None
            report["errores"].append("Falta Unsloth en el entorno aislado.")
            report["ok"] = False
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
    runtime_versions=installed_runtime_versions(bool(cfg.get("qlora")),
                                                 cuda_build=torch.version.cuda)
    resume_path=prepare_training_run(cfg,runtime_versions=runtime_versions)
    if resume_path:
        manifest=Path(cfg["output"])/"fresita_checkpoint_manifest.json"
        if json.loads(manifest.read_text(encoding="utf-8")).get("version")==1:
            print("AVISO: checkpoint heredado sin huella de versiones. "
                  "La compatibilidad del entorno NO se ha verificado.",flush=True)
        else:
            print("REANUDACIÓN VALIDADA: receta, datasets y versiones del entorno coinciden",
                  flush=True)
    dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    kwargs={"dtype":dtype,"trust_remote_code":False}
    if cfg.get("qlora"):
        kwargs["quantization_config"]=BitsAndBytesConfig(
            load_in_4bit=True,bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=dtype,bnb_4bit_use_double_quant=True)
        kwargs["device_map"]="auto"
    print("Iniciando entrenamiento CUDA con:",torch.cuda.get_device_name(0),
          "| backend:",backend,flush=True)
    rank=int(cfg["rank"])
    if backend == "unsloth":
        model,tok=run_training_stage(
            "carga",load_unsloth_model,cfg["model"],rank,bool(cfg.get("qlora")),
            FastLanguageModel)
        peft=None  # Unsloth ya aplicó el adaptador: no duplicar PEFT en SFTTrainer.
    else:
        model=run_training_stage("carga",AutoModelForCausalLM.from_pretrained,cfg["model"],**kwargs)
        tok=AutoTokenizer.from_pretrained(cfg["model"],trust_remote_code=False)
        peft=LoraConfig(r=rank,lora_alpha=rank*2,task_type="CAUSAL_LM",target_modules="all-linear")
    model.config.use_cache=False
    if tok.pad_token is None:tok.pad_token=tok.eos_token
    steps=int(cfg["steps"])
    opts=SFTConfig(**sft_training_kwargs(dict(
       output_dir=cfg["output"],max_steps=steps,
       per_device_train_batch_size=1,per_device_eval_batch_size=1,
       gradient_accumulation_steps=4,eval_accumulation_steps=1,
       max_length=256,learning_rate=float(cfg["lr"]),dataset_text_field="text",
       gradient_checkpointing=True,logging_steps=5,
       eval_strategy="steps" if eval_ds is not None else "no",
       eval_steps=max(1,steps//5) if eval_ds is not None else None,
       report_to="none",bf16=dtype==torch.bfloat16,fp16=dtype==torch.float16,
       ),steps,cfg.get("checkpoint_interval",0)))
    class HistoryCallback(TrainerCallback):
        def on_log(self, args, state, control, logs=None, **kwargs):
            append_metrics(Path(cfg["output"])/"metricas_historial.jsonl",
                           int(state.global_step), logs or {})

    trainer=run_training_stage("preparacion",SFTTrainer,model=model,args=opts,train_dataset=ds,
        eval_dataset=eval_ds,processing_class=tok,peft_config=peft,
        callbacks=[HistoryCallback()])
    if resume_path:
        run_training_stage("entrenamiento",trainer.train,
                           resume_from_checkpoint=str(resume_path))
    else:
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
