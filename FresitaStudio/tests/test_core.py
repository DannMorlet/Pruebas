import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fresita_core as core

class FresitaTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.old=core.BASE
        core.BASE=Path(self.temp.name)
    def tearDown(self):
        core.BASE=self.old
        self.temp.cleanup()
    def test_normalizar(self):
        self.assertIn("Usuario: hola",core.normalize({"instruction":"hola","output":"qué onda"}))
    def test_dataset_y_limpieza(self):
        raw=core.BASE/"datos.jsonl"
        raw.write_text("\n".join([
          json.dumps({"text":"Texto de ejemplo largo"},ensure_ascii=False),
          json.dumps({"text":"Texto de ejemplo largo"},ensure_ascii=False),
          json.dumps({"text":"Otro ejemplo largo"},ensure_ascii=False)]),encoding="utf-8")
        target,count=core.import_dataset(raw)
        self.assertEqual(count,3)
        clean,n=core.clean_dataset(target)
        self.assertEqual(n,2)
        self.assertNotEqual(target,clean)
    def test_pesos_safetensors(self):
        header=json.dumps({"w":{"shape":[2,3],"dtype":"F32","data_offsets":[0,24]}}).encode()
        (core.BASE/"test.safetensors").write_bytes(len(header).to_bytes(8,"little")+header+b"\x00"*24)
        self.assertEqual(core.inspect_safetensors(core.BASE),(6,1))
    def test_receta(self):
        path=core.save_recipe({"modelo":"Qwen/Qwen3-0.6B"})
        self.assertTrue(path.exists())

    def test_auditoria_y_deduplicacion(self):
        source=core.BASE/"auditoria.jsonl"
        source.write_text("\n".join([
            json.dumps({"text":"Texto de entrenamiento A"}),
            json.dumps({"text":"  texto   de entrenamiento a "}),
            json.dumps({"text":"Texto de entrenamiento B"}),
            "esto no es json",
            json.dumps({"text":"breve"})]),encoding="utf-8")
        stats=core.audit_dataset(source)
        self.assertEqual(stats["validos"],3)
        self.assertEqual(stats["unicos"],2)
        self.assertEqual(stats["duplicados"],1)
        self.assertEqual(stats["invalidos"],2)
        self.assertGreater(stats["caracteres_promedio"],0)

    def test_split_reproducible_sin_fuga(self):
        source=core.BASE/"split.jsonl"
        rows=[{"text":f"Texto de ejemplo número {i:03d} para prueba"} for i in range(20)]
        rows.append(rows[0])
        source.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in rows),encoding="utf-8")
        a,b,nt,nv=core.split_dataset(source)
        self.assertEqual((nt,nv),(18,2))
        ta={json.loads(x)["text"] for x in a.read_text(encoding="utf-8").splitlines()}
        va={json.loads(x)["text"] for x in b.read_text(encoding="utf-8").splitlines()}
        self.assertFalse(ta & va)
        c,d,_,_=core.split_dataset(source)
        self.assertEqual(a.read_bytes(),c.read_bytes())
        self.assertEqual(b.read_bytes(),d.read_bytes())
        self.assertEqual(len(ta|va),20)
        self.assertEqual(len(rows),21)

    def test_split_rechaza_filas_invalidas(self):
        source=core.BASE/"malos.jsonl"
        source.write_text("no es json\n",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"inválidas"):
            core.split_dataset(source)

    def test_split_rechaza_pocos_ejemplos(self):
        source=core.BASE/"cortos.jsonl"
        source.write_text(json.dumps({"text":"Texto suficientemente largo"}),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"al menos 10"):
            core.split_dataset(source)

    def test_validacion_independiente(self):
        a=core.BASE/"train.jsonl"
        b=core.BASE/"val.jsonl"
        a.write_text('{"text":"ejemplo para entrenar A"}\n{"text":"ejemplo para entrenar B"}\n',encoding="utf-8")
        b.write_text('{"text":"ejemplo de validación C"}\n',encoding="utf-8")
        self.assertEqual(core.validate_eval_pair(a,b),
            {"entrenamiento_unicos":2,"validacion_unicos":1})

    def test_validacion_detecta_fuga(self):
        a=core.BASE/"train.jsonl"
        b=core.BASE/"val.jsonl"
        a.write_text('{"text":"ejemplo para entrenar A"}\n{"text":"ejemplo para entrenar B"}\n',encoding="utf-8")
        b.write_text('{"text":" EJEMPLO  PARA entrenar a "}\n',encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"Fuga"):
            core.validate_eval_pair(a,b)

    def test_validacion_rechaza_mismo_archivo(self):
        a=core.BASE/"datos.jsonl"
        a.write_text('{"text":"ejemplo largo"}\n',encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"distintos"):
            core.validate_eval_pair(a,a)

    def test_resumen_evaluacion_sin_datos_privados(self):
        import math
        report=core.evaluation_summary({"eval_loss":math.log(2),"eval_samples":"privado"},4,25)
        self.assertAlmostEqual(report["perplejidad"],2.0)
        self.assertEqual(report["ejemplos_validacion"],4)
        self.assertNotIn("eval_samples",report)
        self.assertTrue(report["evaluacion_valida"])

    def test_resumen_evaluacion_no_finito(self):
        report=core.evaluation_summary({"eval_loss":float("nan")},1,5)
        self.assertIsNone(report["eval_loss"])
        self.assertIsNone(report["perplejidad"])
        self.assertFalse(report["evaluacion_valida"])
        self.assertNotIn("NaN",json.dumps(report,allow_nan=False))
