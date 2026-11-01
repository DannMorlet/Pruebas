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
