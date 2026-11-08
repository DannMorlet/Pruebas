"""Pruebas sin CUDA ni modelo remoto para el benchmark de velocidad."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_speed import summarize_speed, benchmark_local
from fresita_resources import ResourceSampler

class SpeedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.dataset = self.root/"casos.jsonl"
        self.dataset.write_text(json.dumps({"pregunta":"Pregunta privada",
            "referencia":"Referencia secreta", "categoria":"es_mx"})+"\n", encoding="utf-8")
    def tearDown(self):
        self.temp.cleanup()
    def test_agregados(self):
        x = summarize_speed([0.1,0.2],[10,20])
        self.assertEqual(x["latencia_p95_s"],0.2)
        self.assertEqual(x["tokens_salida_por_s_extremo_a_extremo"],100)
    def test_sin_usage(self):
        x = summarize_speed([0.1,0.2],[10,None])
        self.assertIsNone(x["tokens_salida_por_s_extremo_a_extremo"])
        self.assertEqual(x["muestras_con_usage"],1)
    def test_no_acepta_duracion_falsa(self):
        for value in (0,-1,float("nan"),float("inf"),True):
            with self.subTest(value=value),self.assertRaises(ValueError):
                summarize_speed([value],[5])
    def test_privacidad_y_reporte(self):
        calls=[]
        ticks=iter([10.0,10.2])
        def fake(host,port,model,prompt,max_tokens):
            calls.append((host,prompt))
            return "Respuesta", 12
        output,path,report=benchmark_local(self.dataset,self.root/"pred",
            workspace=self.root,endpoint="http://127.0.0.1:1234/v1",
            model="modelo",requester=fake,clock=lambda:next(ticks))
        self.assertTrue(output.exists() and path.exists())
        self.assertEqual(report["muestras_con_usage"],1)
        self.assertEqual(report["tokens_salida_por_s_extremo_a_extremo"],60)
        self.assertEqual(calls,[("127.0.0.1","Pregunta privada")])
        saved=path.read_text(encoding="utf-8")
        self.assertNotIn("Pregunta privada",saved)
        self.assertNotIn("Referencia secreta",saved)
    def test_cancelacion_no_guarda_reporte(self):
        with self.assertRaises(InterruptedError):
            benchmark_local(self.dataset,self.root/"pred",
                workspace=self.root,endpoint="http://127.0.0.1:1234/v1",
                model="modelo",cancelled=lambda:True,
                requester=lambda *args: ("nunca",5))
        self.assertFalse((self.root/"experiments").exists())
    def test_rechaza_endpoint_remoto(self):
        with self.assertRaises(ValueError):
            benchmark_local(self.dataset,self.root/"pred",workspace=self.root,
                endpoint="http://192.168.1.10:1234/v1",model="modelo",
                requester=lambda *args: ("nunca",5))

class ResourceTests(unittest.TestCase):
    def test_mediciones_globales_sin_atribucion(self):
        snapshots = iter([
            {"gpu_used_mib": 2100, "gpu_total_mib": 8192,
             "ram_used_mib": 9000, "ram_total_mib": 32768},
            {"gpu_used_mib": 2900, "gpu_total_mib": 8192,
             "ram_used_mib": 9500, "ram_total_mib": 32768},
            {"gpu_used_mib": 2200, "gpu_total_mib": 8192,
             "ram_used_mib": 9200, "ram_total_mib": 32768}
        ])
        sampler = ResourceSampler(probe=lambda: next(snapshots))
        for _ in range(3):
            sampler.capture()
        x = sampler.summary()
        self.assertEqual(x["gpu_global_base_mib"], 2100)
        self.assertEqual(x["gpu_global_pico_mib"], 2900)
        self.assertEqual(x["gpu_global_delta_pico_base_mib"], 800)
        self.assertEqual(x["ram_global_pico_mib"], 9500)
        self.assertIn("no atribuibles", x["advertencia_recursos"])

    def test_no_inventa_telemetria(self):
        sampler = ResourceSampler(probe=lambda: {})
        sampler.capture()
        x = sampler.summary()
        self.assertIsNone(x["gpu_global_pico_mib"])
        self.assertIsNone(x["ram_global_pico_mib"])
        self.assertEqual(x["gpu_global_muestras"], 0)

    def test_ignora_muestras_invalidas(self):
        sampler = ResourceSampler(probe=lambda: {
            "gpu_used_mib": True, "gpu_total_mib": 8192,
            "ram_used_mib": -2, "ram_total_mib": 32000})
        sampler.capture()
        self.assertEqual(sampler.summary()["gpu_global_muestras"], 0)
        with self.assertRaises(ValueError):
            ResourceSampler(interval=0)

    def test_integracion_reporte_global_privado(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = root/"casos.jsonl"
            dataset.write_text(json.dumps({
                "pregunta": "Pregunta sensible", "referencia": "Referencia privada",
                "categoria": "es_mx"})+"\n", encoding="utf-8")
            ticks = iter([1.0, 1.5])
            class FakeSampler:
                def start(self):
                    pass
                def stop(self):
                    return {"gpu_global_pico_mib": 3100,
                            "ram_global_pico_mib": 9400,
                            "advertencia_recursos": "Medición global, no atribuible"}
            output, path, report = benchmark_local(
                dataset, root/"pred", workspace=root,
                endpoint="http://127.0.0.1:1234/v1", model="modelo",
                requester=lambda *args: ("Respuesta", 4),
                clock=lambda: next(ticks), sampler_factory=FakeSampler)
            self.assertEqual(report["gpu_global_pico_mib"], 3100)
            saved = path.read_text(encoding="utf-8")
            self.assertNotIn("Pregunta sensible", saved)
            self.assertNotIn("Referencia privada", saved)
            self.assertTrue(output.exists())
