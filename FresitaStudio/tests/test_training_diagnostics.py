"""Pruebas sin CUDA de diagnósticos de RAM/VRAM."""
from contextlib import redirect_stderr
from io import StringIO
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_training_diagnostics import diagnose_memory_error, run_training_stage


class MemoryDiagnosticsTests(unittest.TestCase):
    def test_cuda_oom_en_carga(self):
        result = diagnose_memory_error(
            RuntimeError("CUDA out of memory. Ruta privada C:/secretos"), "carga")
        self.assertEqual(result["codigo"], "CUDA_SIN_VRAM")
        self.assertEqual(result["etapa"], "carga")
        self.assertNotIn("secretos", json.dumps(result))

    def test_cublas_alloc_failed(self):
        result = diagnose_memory_error(
            RuntimeError("CUBLAS_STATUS_ALLOC_FAILED when calling cublasCreate"), "entrenamiento")
        self.assertEqual(result["codigo"], "CUDA_SIN_VRAM")

    def test_cudnn_alloc_failed_sin_filtrar_datos(self):
        result = diagnose_memory_error(
            RuntimeError("CUDNN_STATUS_ALLOC_FAILED en C:/privado/pesos"), "entrenamiento")
        self.assertEqual(result["codigo"], "CUDA_SIN_VRAM")
        self.assertNotIn("privado", json.dumps(result))

    def test_cuda_error_memory_allocation_sin_filtrar_datos(self):
        result = diagnose_memory_error(
            RuntimeError("CUDA error: cudaErrorMemoryAllocation en C:/privado/modelo"), "carga")
        self.assertEqual(result["codigo"], "CUDA_SIN_VRAM")
        self.assertNotIn("privado", json.dumps(result))

    def test_cuda_error_out_of_memory(self):
        result = diagnose_memory_error(
            RuntimeError("CUDA error: out of memory en C:/privado/modelo"), "preparacion")
        self.assertEqual(result["codigo"], "CUDA_SIN_VRAM")
        self.assertNotIn("privado", json.dumps(result))

    def test_cpu_allocator_ram_agotada_sin_filtrar_datos(self):
        for message in (
            "DefaultCPUAllocator: not enough memory en C:/privado/dataset.jsonl",
            "DefaultCPUAllocator: can\u0027t allocate memory en C:/privado/modelo",
            "std::bad_alloc en C:/privado/pesos",
        ):
            with self.subTest(message=message.split(" en ")[0]):
                result = diagnose_memory_error(RuntimeError(message), "entrenamiento")
                self.assertEqual(result["codigo"], "RAM_AGOTADA")
                self.assertNotIn("privado", json.dumps(result))

    def test_ram_agotada(self):
        result = diagnose_memory_error(MemoryError("datos secretos"), "preparacion")
        self.assertEqual(result["codigo"], "RAM_AGOTADA")
        self.assertNotIn("secretos", json.dumps(result))

    def test_error_ordinario_no_se_disfraza(self):
        self.assertIsNone(diagnose_memory_error(RuntimeError("Archivo no encontrado"), "carga"))
        self.assertIsNone(diagnose_memory_error(ValueError("CUDA out of memory"), "carga"))
        self.assertIsNone(diagnose_memory_error(RuntimeError("out of memory"), "carga"))

    def test_operacion_correcta_sin_mensaje(self):
        buffer = StringIO()
        with redirect_stderr(buffer):
            result = run_training_stage("evaluacion", lambda x: x + 1, 4)
        self.assertEqual(result, 5)
        self.assertEqual(buffer.getvalue(), "")

    def test_error_oom_se_propaga_y_no_filtra_ruta(self):
        buffer = StringIO()
        original = RuntimeError("CUDA out of memory en C:/privado/dataset.jsonl")
        def failing():
            raise original
        with redirect_stderr(buffer):
            with self.assertRaises(RuntimeError) as caught:
                run_training_stage("entrenamiento", failing)
        self.assertIs(caught.exception, original)
        self.assertIn("CUDA_SIN_VRAM", buffer.getvalue())
        self.assertNotIn("privado", buffer.getvalue())

    def test_error_no_memoria_se_propaga_sin_diagnostico(self):
        buffer = StringIO()
        with redirect_stderr(buffer):
            with self.assertRaisesRegex(RuntimeError, "otro fallo"):
                run_training_stage("carga", lambda: (_ for _ in ()).throw(RuntimeError("otro fallo")))
        self.assertEqual(buffer.getvalue(), "")

    def test_etapa_desconocida_no_ejecuta(self):
        called = []
        with self.assertRaises(ValueError):
            run_training_stage("otra", lambda: called.append(True))
        self.assertEqual(called, [])


if __name__ == "__main__":
    unittest.main()
