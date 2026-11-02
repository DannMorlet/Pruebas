"""Pruebas del diagnóstico opcional Unsloth: sin CUDA, pip ni red."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_unsloth import (
    PREFIX, PACKAGES, PROBE_SCRIPT, check_unsloth,
    format_unsloth_report, parse_probe_output,
)

def sample(installed=True):
    return {
        "python":"3.12.9", "bits":64,
        "packages":{name:("2026.10.1" if name == "unsloth" and installed
                          else "2.14.1" if name == "torch"
                          else None) for name in PACKAGES},
        "cuda_build":"13.2", "cuda_available":True,
        "gpu":"NVIDIA RTX 5060", "torch_importable":True
    }

class UnslothCheckTests(unittest.TestCase):
    def test_parseo(self):
        self.assertEqual(parse_probe_output(PREFIX+json.dumps(sample())),sample())
    def test_rechaza_duplicados(self):
        line=PREFIX+json.dumps(sample())
        with self.assertRaises(ValueError):
            parse_probe_output(line+"\n"+line)
    def test_rechaza_respuesta_gigante(self):
        with self.assertRaises(ValueError):
            parse_probe_output("x"*200001)
    def test_rechaza_campos_incompletos(self):
        report=sample()
        del report["packages"]["unsloth_zoo"]
        with self.assertRaises(ValueError):
            parse_probe_output(PREFIX+json.dumps(report))
    def test_rechaza_tipos_invalidos(self):
        report=sample()
        report["cuda_available"]="yes"
        with self.assertRaises(ValueError):
            parse_probe_output(PREFIX+json.dumps(report))
    def test_rechaza_version_larga(self):
        report=sample()
        report["packages"]["unsloth"]="a"*81
        with self.assertRaises(ValueError):
            parse_probe_output(PREFIX+json.dumps(report))
    def test_rechaza_json_malformado(self):
        with self.assertRaises(ValueError):
            parse_probe_output(PREFIX+"{invalido")
    def test_sin_venv_no_ejecuta(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                check_unsloth(workspace=d,runner=lambda *a,**k:self.fail("No ejecutar"))
    def test_solo_lectura_sin_instalacion(self):
        with tempfile.TemporaryDirectory() as d:
            python=Path(d)/".venv"/"Scripts"/"python.exe"
            python.parent.mkdir(parents=True)
            python.write_bytes(b"simulado")
            calls=[]
            def runner(command, **kw):
                calls.append((command,kw))
                return subprocess.CompletedProcess(command,0,
                    PREFIX+json.dumps(sample())+"\n","")
            report=check_unsloth(workspace=d,runner=runner)
            self.assertEqual(report["packages"]["unsloth"],"2026.10.1")
            command,kwargs=calls[0]
            self.assertEqual(command[:3],[str(python),"-I","-c"])
            self.assertNotIn("pip",str(command))
            self.assertNotIn("install",str(command))
            self.assertEqual(kwargs["timeout"],60)
            self.assertNotIn("shell",kwargs)
            self.assertEqual(len(calls),1)
    def test_proceso_fallido_no_se_acepta(self):
        with tempfile.TemporaryDirectory() as d:
            python=Path(d)/".venv"/"Scripts"/"python.exe"
            python.parent.mkdir(parents=True)
            python.touch()
            with self.assertRaises(RuntimeError):
                check_unsloth(workspace=d,runner=lambda cmd,**kw:
                    subprocess.CompletedProcess(cmd,1,PREFIX+json.dumps(sample()),"privado"))
    def test_formato_no_muestra_datos_ajenos(self):
        report=sample()
        report["secreto"]="TOKEN_PRIVADO"
        result=format_unsloth_report(report)
        self.assertIn("sin validar entrenamiento",result)
        self.assertNotIn("TOKEN_PRIVADO",result)
        self.assertIn("TRL/PEFT",result)
    def test_no_confunde_ausente_con_compatible(self):
        result=format_unsloth_report(sample(False))
        self.assertIn("no instalado",result)
        self.assertIn("NO confirma",result)
    def test_script_no_importa_unsloth_ni_instala(self):
        self.assertNotIn("import unsloth\n",PROBE_SCRIPT)
        self.assertNotIn("pip install",PROBE_SCRIPT)
        self.assertIn("metadata.version",PROBE_SCRIPT)
