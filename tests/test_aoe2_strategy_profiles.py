"""Pruebas del planificador (solo lógica; no juego ni LM Studio)."""
import unittest

from aoe2.strategy_profiles import GEMINI_ECONOMY, propose


class StrategyProfilesTest(unittest.TestCase):
    def test_solo_tres_perfiles_y_sin_octava_ia(self):
        for name in ["Nutella", "Gemini", "Copilot"]:
            self.assertEqual(propose(name, {"villagers": 10})["agent"], name)
        with self.assertRaises(ValueError):
            propose("Gemma", {})

    def test_todas_rescatan_un_aldeano(self):
        for name in ["Nutella", "Gemini", "Copilot"]:
            self.assertEqual(propose(name, {"villagers": 1})["action"], "recover")

    def test_todas_defienden_amenaza_critica(self):
        for name in ["Nutella", "Gemini", "Copilot"]:
            p = propose(name, {"villagers": 15, "enemy_pressure": 3})
            self.assertEqual(p["action"], "defend")

    def test_gemini_porcentajes_suman_100(self):
        for age, target in GEMINI_ECONOMY.items():
            self.assertEqual(sum(target.values()), 100)
            p = propose("Gemini", {"age": age, "villagers": 15})
            self.assertEqual(p["economic_targets_percent"], target)

    def test_gemini_retirada_30(self):
        p = propose("Gemini", {
            "villagers": 12, "housing_margin": 5, "enemy_pressure": 1,
            "army_hp_percent": 30
        })
        self.assertEqual(p["action"], "retreat")

    def test_nutella_solo_hostiga_objetivos_visibles(self):
        p = propose("Nutella", {
            "villagers": 12, "own_army": 5, "enemy_pressure": 0,
            "targets_visible": True, "enemy_vulnerabilities": ["exposed_gold"]
        })
        self.assertEqual(p["action"], "harass")
        p2 = propose("Nutella", {
            "villagers": 12, "own_army": 5, "enemy_pressure": 0,
            "targets_visible": False, "enemy_vulnerabilities": ["exposed_gold"]
        })
        self.assertNotEqual(p2["action"], "harass")

    def test_copilot_tiene_prioridades_adaptativas(self):
        p = propose("Copilot", {
            "villagers": 12, "own_army": 10, "housing_margin": 5,
            "explored_percent": 70, "food": 200, "can_advance_age": True
        })
        self.assertEqual(p["action"], "age_up")

    def test_nunca_ejecuta_ni_hace_trampa(self):
        for name in ["Nutella", "Gemini", "Copilot"]:
            p = propose(name, {"age": "imperial", "villagers": 11})
            self.assertIs(p["implemented_in_game"], False)
            self.assertIs(p["uses_cheats"], False)
            self.assertIs(p["uses_hidden_information"], False)


if __name__ == "__main__":
    unittest.main()
