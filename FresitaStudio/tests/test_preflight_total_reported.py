"""Regresión: CUDA no debe aceptar memoria reportada mayor que la física."""
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_train_preflight import REQUIRED, inspect_environment


class MemoriaCUDAInconsistenteTests(unittest.TestCase):
    def test_total_reportado_mayor_que_capacidad_fisica(self):
        fisica = 8 * 1024**3
        cuda = SimpleNamespace(
            is_available=lambda: True,
            get_device_name=lambda index: "NVIDIA RTX 5060",
            get_device_properties=lambda index: SimpleNamespace(total_memory=fisica),
            mem_get_info=lambda index: (7 * 1024**3, 9 * 1024**3),
        )
        torch = SimpleNamespace(cuda=cuda)
        report = inspect_environment(
            version_lookup=lambda package: "1.0",
            torch_module=torch,
        )
        self.assertTrue(report["ok"])
        self.assertTrue(report["cuda_disponible"])
        self.assertEqual(report["vram_total_mib"], 8192)
        self.assertIsNone(report["vram_libre_mib"])
        self.assertTrue(any("VRAM libre inválida" in aviso for aviso in report["avisos"]))

    def test_total_reportado_menor_a_un_mib_se_descarta(self):
        fisica = 8 * 1024**3
        for reportado in (1, 1024, 1024**2 - 1):
            with self.subTest(total_reportado=reportado):
                cuda = SimpleNamespace(
                    is_available=lambda: True,
                    get_device_name=lambda index: "NVIDIA RTX 5060",
                    get_device_properties=lambda index: SimpleNamespace(total_memory=fisica),
                    mem_get_info=lambda index: (0, reportado),
                )
                report = inspect_environment(
                    version_lookup=lambda package: "1.0",
                    torch_module=SimpleNamespace(cuda=cuda),
                )
                self.assertTrue(report["ok"])
                self.assertTrue(report["cuda_disponible"])
                self.assertEqual(report["vram_total_mib"], 8192)
                self.assertIsNone(report["vram_libre_mib"])
                self.assertTrue(any("VRAM libre inválida" in aviso for aviso in report["avisos"]))

    def test_total_reportado_igual_al_fisico_se_acepta(self):
        fisica = 8 * 1024**3
        cuda = SimpleNamespace(
            is_available=lambda: True,
            get_device_name=lambda index: "NVIDIA RTX 5060",
            get_device_properties=lambda index: SimpleNamespace(total_memory=fisica),
            mem_get_info=lambda index: (6 * 1024**3, fisica),
        )
        report = inspect_environment(
            version_lookup=lambda package: "1.0",
            torch_module=SimpleNamespace(cuda=cuda),
        )
        self.assertEqual(report["vram_libre_mib"], 6144)


if __name__ == "__main__":
    unittest.main()
