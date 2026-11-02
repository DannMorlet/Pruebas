"""Pruebas de diagnóstico sin CUDA ni descargas."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_train_check import (
    PREFIX, check_training_environment, format_preflight_report,
    parse_preflight_output,
)

def sample(ok=True):
    return {"ok":ok,"python":"3.12.9","bits":64,"cuda_disponible":ok,
            "gpu":"NVIDIA GeForce RTX 5060" if ok else None,
            "vram_total_mib":8192 if ok else None,
            "vram_libre_mib":6500 if ok else None,
            "dependencias":{"torch":"2.14.1","trl":"0.28.0","peft":"0.18.0"},
            "errores":[] if ok else ["Falta la dependencia: torch"],
            "avisos":["No se entrenó."]}

class TrainingCheckTests(unittest.TestCase):
    def test_parseo_ok(self):
        report=parse_preflight_output(PREFIX + " " + json.dumps(sample()) + "\n")
        self.assertTrue(report["ok"])
    def test_parseo_rechaza_duplicado(self):
        line=PREFIX+" "+json.dumps(sample())+"\n"
        with self.assertRaises(ValueError):
            parse_preflight_output(line+line)
    def test_parseo_rechaza_json_invalido(self):
        with self.assertRaises(ValueError):
            parse_preflight_output(PREFIX+" {no-json}")
    def test_parseo_rechaza_respuesta_sin_reporte(self):
        with self.assertRaises(ValueError):
            parse_preflight_output("Error CUDA")
    def test_parseo_rechaza_estructura(self):
        with self.assertRaises(ValueError):
            parse_preflight_output(PREFIX+" "+json.dumps({"ok":"sí"}))
    def test_no_instala_ni_entrena(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            python=root/".venv"/"Scripts"/"python.exe"
            python.parent.mkdir(parents=True)
            python.write_bytes(b"simulado")
            worker=root/"bundle"/"workers"/"train_lora.py"
            worker.parent.mkdir(parents=True)
            worker.write_text("pass",encoding="utf-8")
            calls=[]
            def runner(command, **kwargs):
                calls.append((command,kwargs))
                cfg=json.loads(Path(command[command.index("--config")+1]).read_text())
                self.assertEqual(cfg,{"qlora":True})
                return subprocess.CompletedProcess(command,1,PREFIX+" "+json.dumps(sample(False))+"\n","")
            result=check_training_environment(True,workspace=root,bundle_root=root/"bundle",runner=runner)
            self.assertFalse(result["ok"])
            self.assertEqual(len(calls),1)
            cmd,kw=calls[0]
            self.assertEqual(cmd[0],str(python))
            self.assertIn("--preflight",cmd)
            self.assertNotIn("--train",cmd)
            self.assertNotIn("shell",kw)
            self.assertEqual(kw["timeout"],90)
    def test_falta_venv_sin_invocar_worker(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(FileNotFoundError,"Falta el Python"):
                check_training_environment(workspace=folder,bundle_root=folder,
                    runner=lambda *args,**kwargs:self.fail("No debe ejecutar"))
    def test_no_confunde_fallo_de_proceso_con_exito(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            python=root/".venv"/"Scripts"/"python.exe";python.parent.mkdir(parents=True);python.touch()
            worker=root/"workers"/"train_lora.py";worker.parent.mkdir(parents=True);worker.touch()
            def runner(cmd,**kw):
                return subprocess.CompletedProcess(cmd,1,PREFIX+" "+json.dumps(sample(True)),"")
            with self.assertRaises(RuntimeError):
                check_training_environment(workspace=root,bundle_root=root,runner=runner)
    def test_formato_espanol_y_sin_datasets(self):
        report=sample(False)
        report["datos_privados"]="MI_DATASET_SECRETO"
        text=format_preflight_report(report)
        self.assertIn("Entorno incompleto",text)
        self.assertIn("torch",text)
        self.assertNotIn("MI_DATASET_SECRETO",text)
    def test_rechaza_modo_no_booleano(self):
        with self.assertRaises(ValueError):
            check_training_environment("QLoRA")
