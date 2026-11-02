"""Instalador opcional Unsloth: CI sin uv, red, paquetes o GPU."""
from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_unsloth_setup import (
    ENV_NAME, POST_INSTALL_CHECK, build_unsloth_setup_plan,
    run_unsloth_setup, SetupCancelled,
)
from fresita_unsloth import check_unsloth

class UnslothSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def plan(self):
        return build_unsloth_setup_plan(workspace=self.root)

    def runner(self, seen, fail_at=None):
        def fake(command, cancel):
            seen.append(command)
            if command[:2] == ["uv", "venv"]:
                python = self.root / ENV_NAME / "Scripts" / "python.exe"
                python.parent.mkdir(parents=True, exist_ok=True)
                python.write_bytes(b"simulado")
            return 1 if fail_at == len(seen) else 0
        return fake

    def test_plan_no_crea_archivos(self):
        plan = self.plan()
        self.assertEqual(len(plan["commands"]), 6)
        self.assertFalse(plan["venv"].exists())
        self.assertEqual(plan["venv"].name, ENV_NAME)

    def test_python313_y_uv_sin_descarga_automatica(self):
        commands = self.plan()["commands"]
        self.assertIn("-3.13", commands[0][1])
        self.assertIn("--no-python-downloads", commands[1][1])
        self.assertEqual(commands[1][1][:2], ["uv", "venv"])

    def test_torchao_antes_de_unsloth(self):
        commands = self.plan()["commands"]
        self.assertIn("torchao", commands[2][1])
        self.assertIn("unsloth", commands[3][1])
        self.assertIn("--torch-backend=auto", commands[3][1])
        self.assertEqual(commands[4][1][:3], ["uv", "pip", "check"])

    def test_postcheck_no_afirma_gpu_operativa(self):
        self.assertIn("torch.version.cuda", POST_INSTALL_CHECK)
        self.assertIn("m.version(name)", POST_INSTALL_CHECK)
        self.assertNotIn("import unsloth\n", POST_INSTALL_CHECK)

    def test_instalacion_simulada_conserva_entorno_original(self):
        old = self.root / ".venv" / "private.txt"
        old.parent.mkdir()
        old.write_text("intacto", encoding="utf-8")
        seen = []
        result = run_unsloth_setup(self.plan(), runner=self.runner(seen), platform="nt")
        self.assertTrue(result["ok"])
        self.assertEqual(len(seen), 6)
        self.assertEqual(old.read_text(encoding="utf-8"), "intacto")
        self.assertFalse((self.root / ENV_NAME / ".fresita-setup-in-progress").exists())

    def test_fallo_revierte_solo_nuevo_venv(self):
        old = self.root / ".venv" / "modelo-privado.bin"
        old.parent.mkdir()
        old.write_bytes(b"pesos")
        with self.assertRaisesRegex(RuntimeError, "No se completó"):
            run_unsloth_setup(self.plan(), runner=self.runner([], fail_at=4), platform="nt")
        self.assertFalse((self.root / ENV_NAME).exists())
        self.assertEqual(old.read_bytes(), b"pesos")

    def test_no_sobrescribe_venv_unsloth(self):
        target = self.root / ENV_NAME
        target.mkdir()
        (target / "pesos.bin").write_bytes(b"private")
        with self.assertRaises(FileExistsError):
            self.plan()
        self.assertEqual((target / "pesos.bin").read_bytes(), b"private")

    def test_cancelacion_sin_crear_venv(self):
        cancel = threading.Event()
        cancel.set()
        with self.assertRaises(SetupCancelled):
            run_unsloth_setup(self.plan(), cancel=cancel,
                runner=lambda *_:self.fail("no ejecutar"), platform="nt")
        self.assertFalse((self.root / ENV_NAME).exists())

    def test_rechaza_destino_ajeno(self):
        plan = self.plan()
        plan["venv"] = self.root / ".venv"
        with self.assertRaises(ValueError):
            run_unsloth_setup(plan, platform="nt")

    def test_diagnostico_puede_seleccionar_entorno_aislado(self):
        with self.assertRaises(FileNotFoundError):
            check_unsloth(workspace=self.root, environment=ENV_NAME)

    def test_diagnostico_rechaza_rutas_arbitrarias(self):
        with self.assertRaises(ValueError):
            check_unsloth(workspace=self.root, environment="../otra")
