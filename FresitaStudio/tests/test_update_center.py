"""Pruebas offline: conmutación, respaldo, validación GPU y no tocar drivers."""
import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fresita_update_center as c

class CenterTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
    def add(self,comp,tag):
        folder=c.component_dir(comp,tag,self.root)
        folder.mkdir(parents=True,exist_ok=True)
        if comp=="llama":
            (folder/"llama-server.exe").write_bytes(b"simulado")
            (folder/"fresita_llama_manifest.json").write_text("{}")
        else:
            p=folder/(".venv" if comp=="trl" else ".venv-unsloth")/"Scripts"/"python.exe"
            p.parent.mkdir(parents=True)
            p.write_bytes(b"simulado")
    def test_activa_y_retrocede_conservando_ambos(self):
        self.add("trl","anterior")
        self.add("trl","nueva")
        c.activate("trl","anterior",self.root)
        c.activate("trl","nueva",self.root)
        self.assertEqual(c.active_tag("trl",self.root),"nueva")
        self.assertEqual(c.rollback("trl",self.root),"anterior")
        self.assertEqual(c.active_tag("trl",self.root),"anterior")
        self.assertTrue((c.component_dir("trl","nueva",self.root)/".venv"/"Scripts"/"python.exe").is_file())
    def test_rechaza_travesia_y_componentes(self):
        with self.assertRaises(ValueError):
            c.component_dir("trl","../malo",self.root)
        with self.assertRaises(ValueError):
            c.component_dir("driver","b1",self.root)
    def test_entorno_manual_se_conserva(self):
        p=c.active_python("trl",self.root)
        self.assertEqual(p,self.root/".venv"/"Scripts"/"python.exe")
    def test_no_hay_rollback_sin_respaldo(self):
        with self.assertRaises(ValueError):
            c.rollback("llama",self.root)
    def test_instalacion_solo_si_driver_compatible(self):
        with self.assertRaises(c.UpdateSkipped):
            c.update_component("llama",root=self.root,platform="nt",driver=590,
                               release={"tag":"b12048"})
        self.assertFalse((self.root/"motores").exists())
    def test_desconocido_no_inicia_descargas(self):
        with self.assertRaises(c.UpdateSkipped):
            c.update_component("trl",root=self.root,platform="nt",driver=0)
    def test_mock_cuda_ok_completa_entorno(self):
        tag=c.TORCH_PROFILE
        folder=c.component_dir("trl",tag,self.root)
        calls=[]
        def runner(command,cancel):
            calls.append(command)
            if "venv" in command:
                p=folder/".venv"/"Scripts"/"python.exe"
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(b"simulado")
            return 0
        def smoke(*args,**kwargs):
            return types.SimpleNamespace(returncode=0)
        bundle=self.root/"bundle"
        bundle.mkdir()
        (bundle/"requirements-train.txt").write_text("trl>=0.20\n")
        outcome=c.update_component("trl",root=self.root,bundle_root=bundle,
                  platform="nt",driver=615,setup_runner=runner,smoke_runner=smoke)
        self.assertIn("activado",outcome)
        self.assertEqual(c.active_tag("trl",self.root),tag)
        self.assertTrue(any("torch==2.14.1" in cmd for cmd in calls))
    def test_cuda_fallido_nunca_activa(self):
        tag=c.TORCH_PROFILE
        self.add("trl",tag)
        def fail(*args,**kwargs):
            return types.SimpleNamespace(returncode=1)
        with self.assertRaises(c.UpdateSkipped):
            c.update_component("trl",root=self.root,platform="nt",
                               driver=615,smoke_runner=fail)
        self.assertIsNone(c.active_tag("trl",self.root))
    def test_frecuncia_24h(self):
        time=dt.datetime(2026,11,2,23,tzinfo=dt.timezone.utc)
        self.assertTrue(c.update_due(self.root,time))
        self.assertFalse(c.update_due(self.root,time+dt.timedelta(hours=12)))
        self.assertTrue(c.update_due(self.root,time+dt.timedelta(hours=25)))
    def test_sin_sistema_windows_no_instala(self):
        with self.assertRaises(c.UpdateSkipped):
            c.update_component("trl",root=self.root,platform="posix",driver=615)
    def test_cuda_real_simulado_rechaza_sin_gpu(self):
        with self.assertRaises(c.UpdateSkipped):
            c.cuda_smoke("python.exe",run=lambda *a,**kw:types.SimpleNamespace(returncode=1))
    def test_activacion_rechaza_entorno_incompleto(self):
        with self.assertRaises(ValueError):
            c.activate("unsloth","u1",self.root)
    def test_configuracion_no_modifica_driver(self):
        self.assertNotIn("pip install nvidia",str(c.update_component))
        self.assertNotIn("nvidia-driver",c.TORCH_PROFILE)

    def test_restaurar_entorno_manual_existente(self):
        manual=self.root/".venv"/"Scripts"/"python.exe"
        manual.parent.mkdir(parents=True)
        manual.write_bytes(b"entorno original")
        self.add("trl","actualizado")
        c.activate("trl","actualizado",self.root)
        self.assertEqual(c.active_tag("trl",self.root),"actualizado")
        self.assertEqual(c.rollback("trl",self.root),"legacy")
        self.assertEqual(c.active_python("trl",self.root),manual)
        self.assertEqual(manual.read_bytes(),b"entorno original")
