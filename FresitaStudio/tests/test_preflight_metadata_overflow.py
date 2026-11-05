"""Regresión: metadatos de paquetes defectuosos no deben romper el diagnóstico."""
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_train_preflight import inspect_environment


class MetadatosOverflowTests(unittest.TestCase):
    def test_overflow_no_filtra_rutas_ni_interrumpe_diagnostico(self):
        secreto = "C:/privado/datasets/cliente.jsonl"

        def lookup(package):
            if package == "trl":
                raise OverflowError(secreto)
            return "1.0"

        cuda = SimpleNamespace(
            is_available=lambda: True,
            get_device_name=lambda index: "NVIDIA RTX 5060",
            get_device_properties=lambda index: SimpleNamespace(total_memory=8 * 1024**3),
        )
        report = inspect_environment(
            version_lookup=lookup,
            torch_module=SimpleNamespace(cuda=cuda),
        )
        self.assertFalse(report["ok"])
        self.assertIsNone(report["dependencias"]["trl"])
        self.assertIn("No se pudo consultar trl: OverflowError", report["errores"])
        self.assertNotIn(secreto, str(report))


if __name__ == "__main__":
    unittest.main()
