"""Regresión: desbordamientos CUDA no deben cerrar el diagnóstico ni filtrar datos."""
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_train_preflight import inspect_environment


class DesbordamientoCUDATests(unittest.TestCase):
    def _cuda(self, *, overflow_en):
        def desbordar(*args):
            raise OverflowError("ruta privada /pesos/cliente/modelo.safetensors")
        return SimpleNamespace(
            is_available=lambda: True,
            get_device_name=lambda index: "NVIDIA RTX 5060",
            get_device_properties=(desbordar if overflow_en == "propiedades" else
                                   lambda index: SimpleNamespace(total_memory=8 * 1024**3)),
            mem_get_info=(desbordar if overflow_en == "memoria" else
                          lambda index: (6 * 1024**3, 8 * 1024**3)),
        )

    def test_desbordamiento_al_consultar_vram_libre(self):
        report = inspect_environment(
            version_lookup=lambda package: "1.0",
            torch_module=SimpleNamespace(cuda=self._cuda(overflow_en="memoria")),
        )
        self.assertTrue(report["ok"])
        self.assertTrue(report["cuda_disponible"])
        self.assertEqual(report["vram_total_mib"], 8192)
        self.assertIsNone(report["vram_libre_mib"])
        self.assertTrue(any("OverflowError" in x for x in report["avisos"]))
        self.assertNotIn("modelo.safetensors", str(report))

    def test_desbordamiento_al_consultar_propiedades(self):
        report = inspect_environment(
            version_lookup=lambda package: "1.0",
            torch_module=SimpleNamespace(cuda=self._cuda(overflow_en="propiedades")),
        )
        self.assertFalse(report["ok"])
        self.assertFalse(report["cuda_disponible"])
        self.assertIsNone(report["gpu"])
        self.assertIsNone(report["vram_total_mib"])
        self.assertTrue(any("OverflowError" in x for x in report["errores"]))
        self.assertNotIn("modelo.safetensors", str(report))


if __name__ == "__main__":
    unittest.main()
