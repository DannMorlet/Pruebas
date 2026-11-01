"""Entrenamiento PEFT/TRL con CUDA; ejecutar únicamente bajo solicitud del usuario."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--config",required=True)
    args=parser.parse_args()
    cfg=json.loads(Path(args.config).read_text(encoding="utf-8"))
    import torch
    from datasets import load_dataset
    from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig
    from peft import LoraConfig
    from trl import SFTConfig,SFTTrainer
    if not torch.cuda.is_available():raise RuntimeError("No se detectó GPU CUDA")
    ds=load_dataset("json",data_files=cfg["dataset"],split="train")
    if "text" not in ds.column_names or len(ds)<2:raise ValueError("Mínimo 2 ejemplos text")
    dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    kwargs={"dtype":dtype,"trust_remote_code":False}
    if cfg.get("qlora"):
        kwargs["quantization_config"]=BitsAndBytesConfig(
            load_in_4bit=True,bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=dtype,bnb_4bit_use_double_quant=True)
        kwargs["device_map"]="auto"
    print("Iniciando entrenamiento CUDA con:",torch.cuda.get_device_name(0),flush=True)
    model=AutoModelForCausalLM.from_pretrained(cfg["model"],**kwargs)
    model.config.use_cache=False
    tok=AutoTokenizer.from_pretrained(cfg["model"],trust_remote_code=False)
    if tok.pad_token is None:tok.pad_token=tok.eos_token
    rank=int(cfg["rank"])
    peft=LoraConfig(r=rank,lora_alpha=rank*2,task_type="CAUSAL_LM",target_modules="all-linear")
    opts=SFTConfig(output_dir=cfg["output"],max_steps=int(cfg["steps"]),
       per_device_train_batch_size=1,gradient_accumulation_steps=4,
       max_length=256,learning_rate=float(cfg["lr"]),dataset_text_field="text",
       gradient_checkpointing=True,logging_steps=5,save_strategy="no",
       report_to="none",bf16=dtype==torch.bfloat16,fp16=dtype==torch.float16)
    trainer=SFTTrainer(model=model,args=opts,train_dataset=ds,processing_class=tok,peft_config=peft)
    trainer.train()
    trainer.save_model(cfg["output"])
    tok.save_pretrained(cfg["output"])
    print("ENTRENAMIENTO COMPLETADO",flush=True)

if __name__=="__main__":
    try:main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
