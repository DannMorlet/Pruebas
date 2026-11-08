"""Pruebas sin CUDA, modelos ni ejecución del código evaluado."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_quality import evaluate_predictions, save_quality_report, _f1

class QualityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.file = self.root / "predicciones.jsonl"
    def tearDown(self):
        self.tmp.cleanup()
    def write(self, rows):
        self.file.write_text("\n".join(json.dumps(row, ensure_ascii=False)
                                        for row in rows) + "\n", encoding="utf-8")
        return evaluate_predictions(self.file)
    def test_espanol_normaliza_mayusculas_y_espacios(self):
        r = self.write([{"categoria": "es_mx", "referencia": "Qué onda, México",
                         "prediccion": "  QUÉ   ONDA,  MÉXICO  "}])
        self.assertEqual(r["metricas"]["es_mx"]["exactitud_normalizada"], 1)
    def test_no_elimina_acentos(self):
        r = self.write([{"categoria": "es_mx", "referencia": "sí", "prediccion": "si"}])
        self.assertEqual(r["exactitud_total"], 0)
    def test_f1_tokens_parcial(self):
        self.assertAlmostEqual(_f1("hola mundo amigo", "hola amigo"), 0.8)
    def test_codigo_python_valido(self):
        r = self.write([{"categoria": "codigo_python", "referencia": "print(1)",
                         "prediccion": "print(1)"}])
        self.assertEqual(r["metricas"]["codigo_python"]["sintaxis_valida"], 1)
        self.assertEqual(r["metricas"]["codigo_python"]["coincidencia_exacta"], 1)
    def test_codigo_sintaxis_invalida(self):
        r = self.write([{"categoria": "codigo_python", "referencia": "print(1)",
                         "prediccion": "def foo(:"}])
        self.assertEqual(r["metricas"]["codigo_python"]["sintaxis_valida"], 0)
    def test_no_ejecuta_codigo(self):
        marker = self.root / "no_debe_crearse.txt"
        code = "open(" + repr(str(marker)) + ", 'w').write('peligro')"
        r = self.write([{"categoria": "codigo_python", "referencia": "pass",
                         "prediccion": code}])
        self.assertEqual(r["metricas"]["codigo_python"]["sintaxis_valida"], 1)
        self.assertFalse(marker.exists())
    def test_filas_invalidas_y_validas(self):
        self.file.write_text('no-json\n' + json.dumps({
            "categoria": "es_mx", "referencia": "respuesta", "prediccion": "respuesta"
        }) + '\n', encoding="utf-8")
        r = evaluate_predictions(self.file)
        self.assertEqual(r["filas_invalidas"], 1)
        self.assertEqual(r["ejemplos_validos"], 1)
    def test_sin_filas_validas_falla(self):
        self.file.write_text('{"dato":"incompleto"}\n', encoding="utf-8")
        with self.assertRaises(ValueError):
            evaluate_predictions(self.file)
    def test_no_guarda_contenido_privado(self):
        secret = "SECRETO-DE-PRUEBA-123"
        r = self.write([{"categoria": "es_mx", "referencia": secret, "prediccion": secret}])
        report_path = save_quality_report(r, self.root)
        data = report_path.read_text(encoding="utf-8")
        self.assertNotIn(secret, data)
        self.assertNotIn(str(self.file), data)
        self.assertEqual(json.loads(data)["ejemplos_validos"], 1)
    def test_archivo_grande_rechazado(self):
        self.file.write_bytes(b"x" * (8 * 1024 * 1024 + 1))
        with self.assertRaises(ValueError):
            evaluate_predictions(self.file)
    def test_maximo_filas(self):
        self.file.write_text('{"categoria":"es_mx"}\n' * 5001, encoding="utf-8")
        with self.assertRaises(ValueError):
            evaluate_predictions(self.file)
    def test_no_inventa_metricas_ausentes(self):
        r = self.write([{"categoria": "es_mx", "referencia": "hola", "prediccion": "hola"}])
        self.assertIsNone(r["metricas"]["codigo_python"]["sintaxis_valida"])
