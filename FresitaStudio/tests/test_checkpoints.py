"""Pruebas CPU de configuración de checkpoints, sin dependencias ML."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_checkpoints import checkpoint_settings


class CheckpointSettingsTests(unittest.TestCase):
    def test_desactivado_por_defecto(self):
        self.assertEqual(checkpoint_settings(100), {"save_strategy": "no"})

    def test_activo_guarda_estado_completo_y_limita_copias(self):
        self.assertEqual(checkpoint_settings(100, 25), {
            "save_strategy": "steps", "save_steps": 25,
            "save_total_limit": 2, "save_only_model": False,
        })

    def test_intervalo_igual_a_pasos(self):
        self.assertEqual(checkpoint_settings(1, 1)["save_steps"], 1)

    def test_rechaza_intervalo_mayor_a_pasos(self):
        with self.assertRaises(ValueError):
            checkpoint_settings(10, 11)

    def test_rechaza_negativos(self):
        for steps, interval in ((0, 0), (-1, 0), (10, -1), (10001, 0)):
            with self.subTest(steps=steps, interval=interval):
                with self.assertRaises(ValueError):
                    checkpoint_settings(steps, interval)

    def test_rechaza_booleanos_y_fracciones(self):
        for steps, interval in ((True, 0), (10, True), (10, 2.5), (10, "5")):
            with self.subTest(steps=steps, interval=interval):
                with self.assertRaises(ValueError):
                    checkpoint_settings(steps, interval)


if __name__ == "__main__":
    unittest.main()
