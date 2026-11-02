"""Instalador guiado: pruebas sin instalar Python, CUDA o paquetes."""
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_train_setup import build_setup_plan, run_setup, SetupCancelled, TORCH_INDEX

class SetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.bundle=self.root/"bundle"
        self.bundle.mkdir()
        (self.bundle/"requirements-train.txt").write_text(
            "trl>=0.20\npeft>=0.17\n", encoding="utf-8")
    def tearDown(self):
        self.tmp.cleanup()
    def plan(self, qlora=False):
        return build_setup_plan(qlora,workspace=self.root,bundle_root=self.bundle)
    def fake_runner(self, seen, fail_at=None):
        def run(command, cancel):
            seen.append(command)
            if "-m" in command and "venv" in command:
                p=self.root/".venv"/"Scripts"/"python.exe"
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(b"simulado")
            return 1 if fail_at==len(seen) else 0
        return run
    def test_no_modifica_nada_al_planear(self):
        plan=self.plan()
        self.assertFalse(plan["venv"].exists())
        self.assertEqual(len(plan["commands"]),4)
    def test_usa_python312_x64_y_cu132_oficial(self):
        plan=self.plan()
        self.assertIn("-3.12",plan["commands"][0][1])
        self.assertIn(TORCH_INDEX,plan["commands"][2][1])
        self.assertIn("torch==2.14.1",plan["commands"][2][1])
    def test_pip_sin_shell_ni_codigo_arbitrario(self):
        plan=self.plan()
        for _,command in plan["commands"][2:]:
            self.assertIn("--isolated",command)
            self.assertIn("--only-binary=:all:",command)
            self.assertIn("--no-input",command)
        self.assertNotIn("unsloth",str(plan["commands"]).lower())
    def test_qlora_incluye_bitsandbytes(self):
        self.assertIn("bitsandbytes",self.plan(True)["commands"][-1][1])
        self.assertNotIn("bitsandbytes",str(self.plan(False)["commands"]))
    def test_instalacion_completa_mock(self):
        seen=[]
        status=[]
        result=run_setup(self.plan(),runner=self.fake_runner(seen),
                         on_stage=status.append,platform="nt")
        self.assertTrue(result["ok"])
        self.assertEqual(len(seen),4)
        self.assertEqual(len(status),4)
        self.assertTrue((self.root/".venv"/"Scripts"/"python.exe").is_file())
        self.assertFalse((self.root/".venv"/".fresita-setup-in-progress").exists())
    def test_fallo_revierte_solo_entorno_nuevo(self):
        private=self.root/"dataset-privado.jsonl"
        private.write_text("datos",encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError,"No se completó"):
            run_setup(self.plan(),runner=self.fake_runner([],fail_at=3),platform="nt")
        self.assertFalse((self.root/".venv").exists())
        self.assertEqual(private.read_text(encoding="utf-8"),"datos")
    def test_entorno_existente_no_se_sobrescribe(self):
        existing=self.root/".venv"
        existing.mkdir()
        secret=existing/"checkpoint-privado"
        secret.write_text("pesos",encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.plan()
        self.assertEqual(secret.read_text(encoding="utf-8"),"pesos")
    def test_cancelacion_no_ejecuta_comandos(self):
        event=threading.Event()
        event.set()
        with self.assertRaises(SetupCancelled):
            run_setup(self.plan(),cancel=event,runner=lambda *_:self.fail("No debe ejecutar"),
                      platform="nt")
        self.assertFalse((self.root/".venv").exists())
    def test_cancelacion_durante_instalacion_revierte(self):
        cancel=threading.Event()
        def runner(command, event):
            if "venv" in command:
                p=self.root/".venv"/"Scripts"/"python.exe"
                p.parent.mkdir(parents=True,exist_ok=True)
                p.touch()
            if "torch==2.14.1" in command:
                cancel.set()
                raise SetupCancelled("Cancelado")
            return 0
        with self.assertRaises(SetupCancelled):
            run_setup(self.plan(),cancel=cancel,runner=runner,platform="nt")
        self.assertFalse((self.root/".venv").exists())
    def test_rechaza_modo_invalido(self):
        with self.assertRaises(ValueError):
            self.plan("QLoRA")
    def test_requiere_archivo_de_dependencias(self):
        (self.bundle/"requirements-train.txt").unlink()
        with self.assertRaises(FileNotFoundError):
            self.plan()
