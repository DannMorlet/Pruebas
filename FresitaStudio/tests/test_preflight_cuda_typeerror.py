"""Regresión: errores TypeError de CUDA no filtran datos ni simulan GPU lista."""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_train_preflight import inspect_environment


class BrokenCuda:
    def is_available(self):
        return True

    def get_device_name(self, index):
        return "GPU simulada"

    def get_device_properties(self, index):
        raise TypeError("C:/privado/datasets/secreto.jsonl")


class CudaTypeErrorTests(unittest.TestCase):
    def test_typeerror_es_seguro_y_no_reporta_cuda_lista(self):
        result = inspect_environment(
            version_lookup=lambda name: "1.0",
            torch_module=SimpleNamespace(cuda=BrokenCuda()),
        )
        self.assertFalse(result["ok"])
        self.assertFalse(result["cuda_disponible"])
        self.assertIsNone(result["gpu"])
        self.assertIsNone(result["vram_total_mib"])
        self.assertIsNone(result["vram_libre_mib"])
        self.assertIn("No se pudo inicializar CUDA: TypeError", result["errores"])
        self.assertNotIn("secreto.jsonl", str(result))


if __name__ == "__main__":
    unittest.main()
