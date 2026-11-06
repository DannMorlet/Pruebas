"""Regresión: TRL no debe recibir save_strategy duplicado al guardar checkpoints."""
import ast
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fresita_checkpoints import sft_training_kwargs


class SFTCheckpointIntegrationTests(unittest.TestCase):
    def test_sin_checkpoints_configuracion_unica(self):
        base = {"output_dir": "ejemplo", "max_steps": 10, "logging_steps": 5}
        result = sft_training_kwargs(base, 10)
        self.assertEqual(result["save_strategy"], "no")
        self.assertEqual(result["max_steps"], 10)
        self.assertNotIn("save_strategy", base)

    def test_con_checkpoints_guarda_estado_completo(self):
        result = sft_training_kwargs({"max_steps": 100}, 100, 25)
        self.assertEqual(result["save_strategy"], "steps")
        self.assertEqual(result["save_steps"], 25)
        self.assertEqual(result["save_total_limit"], 2)
        self.assertIs(result["save_only_model"], False)

    def test_rechaza_colision_de_opciones(self):
        for key in ("save_strategy", "save_steps", "save_total_limit", "save_only_model"):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    sft_training_kwargs({key: "valor"}, 20, 5)

    def test_no_modifica_diccionario_original(self):
        base = {"output_dir": "privado", "max_steps": 20}
        result = sft_training_kwargs(base, 20, 5)
        self.assertEqual(base, {"output_dir": "privado", "max_steps": 20})
        self.assertIsNot(result, base)

    def test_rechaza_intervalo_invalido(self):
        with self.assertRaises(ValueError):
            sft_training_kwargs({"max_steps": 5}, 5, 6)

    def test_worker_usa_un_solo_diccionario_para_sftconfig(self):
        """Detecta la regresión previa sin importar PyTorch, TRL ni CUDA."""
        tree = ast.parse((ROOT / "workers" / "train_lora.py").read_text(encoding="utf-8"))
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "SFTConfig"
        ]
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(calls[0].keywords), 1)
        keyword = calls[0].keywords[0]
        self.assertIsNone(keyword.arg)
        self.assertIsInstance(keyword.value, ast.Call)
        self.assertIsInstance(keyword.value.func, ast.Name)
        self.assertEqual(keyword.value.func.id, "sft_training_kwargs")


if __name__ == "__main__":
    unittest.main()
