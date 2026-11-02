"""VRAM por PID: pruebas deterministas sin GPU ni servidor real."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_resources import ResourceSampler, parse_process_gpu_memory
from fresita_speed import benchmark_local


class ProcessMemoryTests(unittest.TestCase):
    def test_pid_exacto_y_no_otros_procesos(self):
        self.assertEqual(parse_process_gpu_memory("222, 800\n123, 512\n", 123), 512)
        self.assertIsNone(parse_process_gpu_memory("222, 800\n", 123))

    def test_wddm_na_y_filas_ambiguas(self):
        self.assertIsNone(parse_process_gpu_memory("123, N/A\n", 123))
        self.assertIsNone(parse_process_gpu_memory("123, 512\n123, 256\n", 123))
        self.assertIsNone(parse_process_gpu_memory("123, 512 MiB\n", 123))

    def test_rechaza_pid_no_entero_positivo(self):
        for pid in (0, -1, True, 1.5, "123"):
            with self.subTest(pid=pid), self.assertRaises(ValueError):
                parse_process_gpu_memory("123, 100\n", pid)
            with self.subTest(pid=pid), self.assertRaises(ValueError):
                ResourceSampler(pid=pid)

    def test_muestra_pid_no_es_memoria_exclusiva_del_modelo(self):
        snapshots = iter([
            {"gpu_used_mib": 3000, "gpu_total_mib": 8192,
             "gpu_process_used_mib": 1200},
            {"gpu_used_mib": 3500, "gpu_total_mib": 8192,
             "gpu_process_used_mib": 1800},
            {"gpu_used_mib": 3100, "gpu_total_mib": 8192,
             "gpu_process_used_mib": None},
        ])
        sampler = ResourceSampler(pid=123, probe=lambda: next(snapshots))
        for _ in range(3):
            sampler.capture()
        report = sampler.summary()
        self.assertEqual(report["gpu_proceso_pid"], 123)
        self.assertEqual(report["gpu_proceso_muestras"], 2)
        self.assertEqual(report["gpu_proceso_pico_mib"], 1800)
        self.assertEqual(report["gpu_proceso_delta_pico_base_mib"], 600)
        self.assertEqual(report["gpu_global_pico_mib"], 3500)
        self.assertIn("no sólo el modelo", report["advertencia_recursos"])

    def test_sin_pid_no_atribuye_vram(self):
        sampler = ResourceSampler(probe=lambda: {
            "gpu_used_mib": 2500, "gpu_total_mib": 8192,
            "gpu_process_used_mib": 1000})
        sampler.capture()
        report = sampler.summary()
        self.assertIsNone(report["gpu_proceso_pid"])
        self.assertIsNone(report["gpu_proceso_pico_mib"])

    def test_benchmark_propaga_pid_y_no_filtra_datos(self):
        seen = []
        class FakeSampler:
            def __init__(self, pid=None):
                seen.append(pid)
            def start(self):
                pass
            def stop(self):
                return {"gpu_proceso_pid": 123,
                        "gpu_proceso_pico_mib": 1024}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dataset = root / "casos.jsonl"
            dataset.write_text(json.dumps({
                "pregunta": "Pregunta privada",
                "referencia": "Respuesta privada",
                "categoria": "es_mx"}) + "\n", encoding="utf-8")
            ticks = iter([1.0, 1.5])
            output, report_path, report = benchmark_local(
                dataset, root / "pred", workspace=root,
                endpoint="http://127.0.0.1:1234/v1", model="modelo",
                process_pid=123, sampler_factory=FakeSampler,
                requester=lambda *args: ("Respuesta generada", 8),
                clock=lambda: next(ticks))
            self.assertEqual(seen, [123])
            self.assertEqual(report["gpu_proceso_pico_mib"], 1024)
            saved = report_path.read_text(encoding="utf-8")
            self.assertNotIn("Pregunta privada", saved)
            self.assertNotIn("Respuesta privada", saved)
            self.assertTrue(output.exists())

    def test_benchmark_rechaza_pid_invalido(self):
        with self.assertRaises(ValueError):
            benchmark_local(Path("inexistente.jsonl"), Path("pred"),
                workspace=Path("."), endpoint="http://127.0.0.1:1234/v1",
                model="modelo", process_pid=True)


if __name__ == "__main__":
    unittest.main()
