"""Pruebas de diagnóstico CUDA sin instalar ni importar bibliotecas ML."""
from importlib import metadata
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_train_preflight import inspect_environment, REQUIRED


class FakeCuda:
    def __init__(self, available=True, mib=8192):
        self.available = available
        self.mib = mib

    def is_available(self):
        return self.available

    def get_device_name(self, index):
        assert index == 0
        return "NVIDIA RTX de prueba"

    def get_device_properties(self, index):
        assert index == 0
        return SimpleNamespace(total_memory=self.mib * 1024 * 1024)


def versions(name):
    return "1.0.0"


class TrainingPreflightTests(unittest.TestCase):
    def test_lora_cuda_lista_no_carga_pesos(self):
        result = inspect_environment(version_lookup=versions,
                                     torch_module=SimpleNamespace(cuda=FakeCuda()))
        self.assertTrue(result["ok"])
        self.assertTrue(result["cuda_disponible"])
        self.assertEqual(result["vram_total_mib"], 8192)
        self.assertEqual(set(result["dependencias"]), set(REQUIRED))
        self.assertNotIn("bitsandbytes", result["dependencias"])

    def test_qlora_sin_bitsandbytes_se_detiene(self):
        def missing(name):
            if name == "bitsandbytes":
                raise metadata.PackageNotFoundError(name)
            return "1.0"
        result = inspect_environment(True, version_lookup=missing,
                                     torch_module=SimpleNamespace(cuda=FakeCuda()))
        self.assertFalse(result["ok"])
        self.assertIn("Falta la dependencia: bitsandbytes", result["errores"])

    def test_cuda_no_disponible_no_finge_exito(self):
        result = inspect_environment(version_lookup=versions,
                                     torch_module=SimpleNamespace(cuda=FakeCuda(False)))
        self.assertFalse(result["ok"])
        self.assertFalse(result["cuda_disponible"])
        self.assertIsNone(result["gpu"])

    def test_vram_baja_es_aviso_no_estimacion_de_capacidad(self):
        result = inspect_environment(version_lookup=versions,
                                     torch_module=SimpleNamespace(cuda=FakeCuda(True, 6144)))
        self.assertTrue(result["ok"])
        self.assertTrue(any("VRAM limitada" in item for item in result["avisos"]))
        self.assertTrue(any("no garantiza memoria" in item for item in result["avisos"]))

    def test_tipo_qlora_invalido(self):
        with self.assertRaises(ValueError):
            inspect_environment("sí", version_lookup=versions)

    def test_torch_ausente_no_se_importa(self):
        def missing(name):
            if name == "torch":
                raise metadata.PackageNotFoundError(name)
            return "1.0"
        result = inspect_environment(version_lookup=missing)
        self.assertFalse(result["ok"])
        self.assertIn("Falta la dependencia: torch", result["errores"])
        self.assertFalse(result["cuda_disponible"])


if __name__ == "__main__":
    unittest.main()
