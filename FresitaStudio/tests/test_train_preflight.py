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


class FakeCudaMemory(FakeCuda):
    def __init__(self, free_mib=4096, total_mib=8192, error=None):
        super().__init__(True, total_mib)
        self.free_mib = free_mib
        self.total_mib = total_mib
        self.error = error
        self.calls = []

    def mem_get_info(self, index):
        self.calls.append(index)
        if self.error:
            raise self.error
        return (self.free_mib * 1024**2, self.total_mib * 1024**2)


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

    def test_error_tipo_metadatos_no_filtra_ruta_privada(self):
        secreto = "C:/Usuarios/privado/dataset.jsonl"

        def broken(name):
            if name == "trl":
                raise TypeError(secreto)
            return "1.0"

        result = inspect_environment(version_lookup=broken,
                                     torch_module=SimpleNamespace(cuda=FakeCuda()))
        self.assertFalse(result["ok"])
        self.assertIsNone(result["dependencias"]["trl"])
        self.assertIn("No se pudo consultar trl: TypeError", result["errores"])
        self.assertNotIn(secreto, str(result))

    def test_cuda_memoria_total_invalida_no_finge_exito(self):
        for total in (0, -1, None, "8192"):
            with self.subTest(total=total):
                cuda = FakeCuda()
                cuda.get_device_properties = lambda index, value=total: SimpleNamespace(total_memory=value)
                result = inspect_environment(version_lookup=versions,
                                             torch_module=SimpleNamespace(cuda=cuda))
                self.assertFalse(result["ok"])
                self.assertFalse(result["cuda_disponible"])
                self.assertIsNone(result["gpu"])
                self.assertIsNone(result["vram_total_mib"])
                self.assertIsNone(result["vram_libre_mib"])
                self.assertTrue(any("No se pudo inicializar CUDA" in e for e in result["errores"]))

    def test_cuda_disponibilidad_no_booleana_se_rechaza(self):
        for value in ("False", 1, None):
            with self.subTest(value=value):
                result = inspect_environment(
                    version_lookup=versions,
                    torch_module=SimpleNamespace(cuda=FakeCuda(value)),
                )
                self.assertFalse(result["ok"])
                self.assertFalse(result["cuda_disponible"])
                self.assertIsNone(result["gpu"])
                self.assertIsNone(result["vram_total_mib"])
                self.assertIn("No se pudo inicializar CUDA: TypeError", result["errores"])

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


    def test_vram_libre_observada_en_gpu_cero(self):
        cuda = FakeCudaMemory(free_mib=4096)
        result = inspect_environment(version_lookup=versions,
                                     torch_module=SimpleNamespace(cuda=cuda))
        self.assertTrue(result["ok"])
        self.assertEqual(result["vram_libre_mib"], 4096)
        self.assertEqual(cuda.calls, [0])

    def test_vram_libre_baja_es_advertencia_no_bloqueo(self):
        result = inspect_environment(version_lookup=versions,
                                     torch_module=SimpleNamespace(cuda=FakeCudaMemory(free_mib=1024)))
        self.assertTrue(result["ok"])
        self.assertEqual(result["vram_libre_mib"], 1024)
        self.assertTrue(any("Menos de 2 GiB" in s for s in result["avisos"]))

    def test_vram_libre_invalida_no_se_inventa(self):
        result = inspect_environment(version_lookup=versions,
                                     torch_module=SimpleNamespace(cuda=FakeCudaMemory(free_mib=9000)))
        self.assertTrue(result["ok"])
        self.assertIsNone(result["vram_libre_mib"])
        self.assertTrue(any("VRAM libre inválida" in s for s in result["avisos"]))

    def test_fallo_de_lectura_vram_libre_no_impide_preflight(self):
        cuda = FakeCudaMemory(error=RuntimeError("No disponible"))
        result = inspect_environment(version_lookup=versions,
                                     torch_module=SimpleNamespace(cuda=cuda))
        self.assertTrue(result["ok"])
        self.assertIsNone(result["vram_libre_mib"])
        self.assertTrue(any("se muestra N/D" in s for s in result["avisos"]))

    def test_sin_api_memoria_libre_permanece_no_disponible(self):
        result = inspect_environment(version_lookup=versions,
                                     torch_module=SimpleNamespace(cuda=FakeCuda()))
        self.assertTrue(result["ok"])
        self.assertIsNone(result["vram_libre_mib"])


    def test_error_cuda_tipo_no_expone_ruta_privada(self):
        secreto = "C:/Usuarios/privado/pesos/modelo.safetensors"
        cuda = FakeCuda()
        def fallo(index):
            raise TypeError(secreto)
        cuda.get_device_name = fallo
        result = inspect_environment(version_lookup=versions,
                                     torch_module=SimpleNamespace(cuda=cuda))
        self.assertFalse(result["ok"])
        self.assertFalse(result["cuda_disponible"])
        self.assertIsNone(result["gpu"])
        self.assertIsNone(result["vram_total_mib"])
        self.assertIn("No se pudo inicializar CUDA: TypeError", result["errores"])
        self.assertNotIn(secreto, str(result))

    def test_nombre_gpu_invalido_no_finge_cuda_lista(self):
        for name in (None, "", "   ", 123):
            with self.subTest(name=name):
                cuda = FakeCuda()
                cuda.get_device_name = lambda index, value=name: value
                result = inspect_environment(
                    version_lookup=versions,
                    torch_module=SimpleNamespace(cuda=cuda),
                )
                self.assertFalse(result["ok"])
                self.assertFalse(result["cuda_disponible"])
                self.assertIsNone(result["gpu"])
                self.assertIsNone(result["vram_total_mib"])
                self.assertIn("No se pudo inicializar CUDA: ValueError", result["errores"])

if __name__ == "__main__":
    unittest.main()
