import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fresita_metrics import compare_summaries,evaluation_fingerprints,read_summary

class FakeBackend:
    def to_str(self):
        return '{"vocab":{"hola":0},"normalizer":"identidad"}'

class FakeTokenizer:
    backend_tokenizer=FakeBackend()

class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.a={"eval_loss":1.5,"validation_sha256":"a"*64,
                "tokenizer_sha256":"b"*64,"eval_max_length":256,"ejemplos_validacion":12}
        self.b=dict(self.a,eval_loss=1.2)
    def tearDown(self):
        self.tmp.cleanup()
    def test_compara_misma_evaluacion(self):
        result=compare_summaries(self.a,self.b)
        self.assertTrue(result["comparable"])
        self.assertEqual(result["mejor"],"B")
        self.assertAlmostEqual(result["delta_b_menos_a"],-0.3)
    def test_compara_empate(self):
        self.assertEqual(compare_summaries(self.a,self.a)["mejor"],"empate")
    def test_rechaza_distinto_dataset(self):
        self.b["validation_sha256"]="c"*64
        self.assertFalse(compare_summaries(self.a,self.b)["comparable"])
    def test_rechaza_distinto_tokenizador(self):
        self.b["tokenizer_sha256"]="d"*64
        self.assertFalse(compare_summaries(self.a,self.b)["comparable"])
    def test_rechaza_distinta_longitud(self):
        self.b["eval_max_length"]=512
        self.assertFalse(compare_summaries(self.a,self.b)["comparable"])
    def test_rechaza_reporte_antiguo(self):
        self.assertFalse(compare_summaries({"eval_loss":1.0},{"eval_loss":0.8})["comparable"])
    def test_rechaza_perdida_no_finita(self):
        self.b["eval_loss"]=float("nan")
        self.assertFalse(compare_summaries(self.a,self.b)["comparable"])
    def test_huellas_sin_textos(self):
        data=self.root/"val.jsonl"
        data.write_text('{"text":"ejemplo confidencial"}\n',encoding="utf-8")
        fingerprints=evaluation_fingerprints(data,FakeTokenizer(),256)
        self.assertEqual(fingerprints["validation_sha256"],hashlib.sha256(data.read_bytes()).hexdigest())
        self.assertEqual(len(fingerprints["tokenizer_sha256"]),64)
        self.assertNotIn("confidencial",json.dumps(fingerprints))
    def test_reporte_filtra_cadenas(self):
        job=self.root/"job";job.mkdir()
        (job/"metricas_validacion.json").write_text(json.dumps(dict(self.a,private="texto privado")),encoding="utf-8")
        summary=read_summary(job)
        self.assertEqual(summary["validation_sha256"],"a"*64)
        self.assertEqual(summary["tokenizer_sha256"],"b"*64)
        self.assertNotIn("private",summary)
    def test_sin_backend_no_comparable(self):
        data=self.root/"val.jsonl";data.write_text('{"text":"ejemplo largo"}\n',encoding="utf-8")
        fp=evaluation_fingerprints(data,object(),256)
        self.assertIsNone(fp["tokenizer_sha256"])
