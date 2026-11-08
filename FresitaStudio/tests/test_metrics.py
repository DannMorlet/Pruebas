import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fresita_metrics import append_metrics,read_history,read_summary,list_experiments

class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()
    def test_historial_sin_texto(self):
        path=self.root/"job-1"/"metricas_historial.jsonl"
        self.assertTrue(append_metrics(path,5,{"loss":1.25,"prompt":"secreto"}))
        self.assertTrue(append_metrics(path,10,{"eval_loss":0.75,"dataset":"privado"}))
        self.assertEqual(read_history(path),[{"paso":5,"loss":1.25},{"paso":10,"eval_loss":0.75}])
        self.assertNotIn("secreto",path.read_text())
    def test_descarta_no_finitos(self):
        path=self.root/"metrics.jsonl"
        self.assertFalse(append_metrics(path,1,{"loss":float("nan")}))
        self.assertFalse(append_metrics(path,True,{"loss":1.0}))
        self.assertFalse(path.exists())
        path.write_text('{"paso":1,"loss":2,"texto":"privado"}\n{"paso":2,"loss":NaN}\nmal\n')
        self.assertEqual(read_history(path),[{"paso":1,"loss":2.0}])
    def test_reporte_numerico(self):
        job=self.root/"job-2";job.mkdir()
        (job/"metricas_validacion.json").write_text(json.dumps({"eval_loss":0.5,"perplejidad":1.65,"pasos_entrenamiento":100,"texto":"privado"}))
        report=read_summary(job)
        self.assertEqual(report["eval_loss"],0.5)
        self.assertNotIn("texto",report)
    def test_lista_local(self):
        a=self.root/"job-2";b=self.root/"job-1";c=self.root/"sin-metricas"
        for p in (a,b,c):p.mkdir()
        (a/"metricas_historial.jsonl").write_text("{}")
        (b/"metricas_validacion.json").write_text("{}")
        self.assertEqual([p.name for p in list_experiments(self.root)],["job-2","job-1"])
    def test_limite_tamano(self):
        path=self.root/"big.jsonl";path.write_bytes(b" "*2_000_001)
        with self.assertRaisesRegex(ValueError,"grande"):read_history(path)
