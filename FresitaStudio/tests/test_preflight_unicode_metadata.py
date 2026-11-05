"""Metadatos Unicode dañados: fallo seguro y sin divulgar rutas."""
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_train_preflight import inspect_environment


class UnicodeMetadataTests(unittest.TestCase):
    def test_unicode_error_does_not_leak_private_path(self):
        secret = "C:/privado/datasets/no-publicar.jsonl"

        def lookup(package):
            if package == "peft":
                raise UnicodeDecodeError("utf-8", b"\\xff", 0, 1, secret)
            return "1.0"

        cuda = SimpleNamespace(is_available=lambda: False)
        report = inspect_environment(version_lookup=lookup, torch_module=SimpleNamespace(cuda=cuda))
        self.assertFalse(report["ok"])
        self.assertIsNone(report["dependencias"]["peft"])
        self.assertIn("No se pudo consultar peft: UnicodeDecodeError", report["errores"])
        self.assertNotIn(secret, str(report))


if __name__ == "__main__":
    unittest.main()
