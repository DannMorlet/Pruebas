"""Pruebas CPU de reanudación: nunca cargan modelos ni datos privados."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_resume import prepare_training_run, recipe_fingerprint


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.dataset = root / "datos.jsonl"
        self.dataset.write_text('{"text":"Un ejemplo de entrenamiento"}\n', encoding="utf-8")
        self.output = root / "salida"
        self.cfg = {
            "model": "Qwen/Qwen3-0.6B", "dataset": str(self.dataset),
            "qlora": False, "rank": 8, "steps": 100, "lr": 0.0001,
            "checkpoint_interval": 25, "output": str(self.output),
        }

    def checkpoint(self, step=25):
        folder = self.output / f"checkpoint-{step}"
        folder.mkdir()
        (folder / "trainer_state.json").write_text(
            json.dumps({"global_step": step}), encoding="utf-8")
        for filename in ("optimizer.pt", "scheduler.pt", "rng_state.pth"):
            (folder / filename).write_bytes(b"estado")
        return folder

    def test_crea_manifiesto_sin_datos_privados(self):
        self.assertIsNone(prepare_training_run(self.cfg))
        content = (self.output / "fresita_checkpoint_manifest.json").read_text()
        self.assertNotIn(str(self.dataset), content)
        self.assertNotIn("Qwen", content)
        self.assertNotIn("Un ejemplo", content)
        self.assertEqual(len(recipe_fingerprint(self.cfg)), 64)

    def test_reanuda_con_estado_completo(self):
        prepare_training_run(self.cfg)
        checkpoint = self.checkpoint()
        self.cfg["resume_checkpoint"] = str(checkpoint)
        self.assertEqual(prepare_training_run(self.cfg), checkpoint.resolve())

    def test_rechaza_dataset_modificado(self):
        prepare_training_run(self.cfg)
        checkpoint = self.checkpoint()
        self.dataset.write_text('{"text":"Contenido modificado"}\n', encoding="utf-8")
        self.cfg["resume_checkpoint"] = str(checkpoint)
        with self.assertRaisesRegex(ValueError, "no coinciden"):
            prepare_training_run(self.cfg)

    def test_rechaza_receta_modificada(self):
        prepare_training_run(self.cfg)
        checkpoint = self.checkpoint()
        self.cfg["resume_checkpoint"] = str(checkpoint)
        self.cfg["rank"] = 16
        with self.assertRaisesRegex(ValueError, "no coinciden"):
            prepare_training_run(self.cfg)

    def test_rechaza_estado_incompleto(self):
        prepare_training_run(self.cfg)
        checkpoint = self.checkpoint()
        (checkpoint / "optimizer.pt").unlink()
        self.cfg["resume_checkpoint"] = str(checkpoint)
        with self.assertRaisesRegex(ValueError, "incompleto"):
            prepare_training_run(self.cfg)

    def test_rechaza_paso_distinto(self):
        prepare_training_run(self.cfg)
        checkpoint = self.checkpoint()
        (checkpoint / "trainer_state.json").write_text('{"global_step": 24}')
        self.cfg["resume_checkpoint"] = str(checkpoint)
        with self.assertRaisesRegex(ValueError, "no coinciden"):
            prepare_training_run(self.cfg)

    def test_rechaza_checkpoint_ajeno(self):
        prepare_training_run(self.cfg)
        self.checkpoint()
        other = Path(self.temp.name) / "ajeno" / "checkpoint-25"
        other.mkdir(parents=True)
        self.cfg["resume_checkpoint"] = str(other)
        with self.assertRaisesRegex(ValueError, "dentro"):
            prepare_training_run(self.cfg)

    def test_no_sobrescribe_salida_existente(self):
        prepare_training_run(self.cfg)
        with self.assertRaisesRegex(ValueError, "no se sobrescribe"):
            prepare_training_run(self.cfg)

    def test_rechaza_heredado_sin_manifiesto(self):
        self.output.mkdir()
        checkpoint = self.checkpoint()
        self.cfg["resume_checkpoint"] = str(checkpoint)
        with self.assertRaisesRegex(ValueError, "manifiesto"):
            prepare_training_run(self.cfg)

    def test_rechaza_reanudacion_sin_guardado(self):
        self.cfg["checkpoint_interval"] = 0
        self.cfg["resume_checkpoint"] = str(self.output / "checkpoint-25")
        with self.assertRaisesRegex(ValueError, "Activa"):
            prepare_training_run(self.cfg)


if __name__ == "__main__":
    unittest.main()
