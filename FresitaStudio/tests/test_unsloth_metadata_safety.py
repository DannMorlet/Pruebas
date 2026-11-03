"""Regresión: el preflight Unsloth no debe imprimir rutas de excepciones."""
import ast
from pathlib import Path
import unittest


WORKER = Path(__file__).resolve().parents[1] / "workers" / "train_lora.py"


class UnslothMetadataSafetyTests(unittest.TestCase):
    def test_metadata_failure_has_sanitized_handler(self):
        tree = ast.parse(WORKER.read_text(encoding="utf-8"))
        handlers = [
            h for node in ast.walk(tree) if isinstance(node, ast.Try)
            for h in node.handlers
            if isinstance(h.type, ast.Tuple)
            and {n.id for n in h.type.elts if isinstance(n, ast.Name)}
            >= {"ValueError", "OSError", "TypeError"}
        ]
        self.assertTrue(handlers, "Debe capturar fallos de metadatos sin traceback")
        handler = handlers[0]
        calls = [
            n for n in ast.walk(handler)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id in {"str", "repr", "print"}
        ]
        self.assertFalse(calls, "No serializar el texto de la excepción privada")


if __name__ == "__main__":
    unittest.main()
