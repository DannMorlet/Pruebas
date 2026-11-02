"""Pruebas sin CUDA ni modelo remoto para el benchmark de velocidad."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_speed import summarize_speed, benchmark_local

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
