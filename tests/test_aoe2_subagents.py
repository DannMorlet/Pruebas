"""Pruebas puras de Tyran/Mazapan: no requieren GPU, LM Studio ni juego."""
import contextlib
import io
import json
import unittest

from aoe2 import subagents_gpu as agents


class TestSubagents(unittest.TestCase):
    def test_solo_dos_subagentes(self):
        self.assertEqual(list(agents.AGENTS), ["Tyran", "Mazapan"])

    def test_identidad_separada(self):
        state = {"aldeanos": 1}
        a = agents.prompt_for("Tyran", state)[0]["content"]
        b = agents.prompt_for("Mazapan", state)[0]["content"]
        self.assertNotEqual(a, b)

    def test_solo_json_de_estado(self):
        self.assertRaises(ValueError, agents.clean_state, "[1,2]")
        self.assertRaises(ValueError, agents.clean_state, "{" + "x" * 10000 + "}")
        self.assertEqual(agents.clean_state('{"aldeanos":1}')["aldeanos"], 1)

    def test_accion_valida(self):
        d = agents.validate_proposal('{"decision":"scout","reason":"Mapa"}')
        self.assertTrue(d["valid"])
        self.assertEqual(d["decision"], "scout")

    def test_rechaza_comandos_no_autorizados(self):
        d = agents.validate_proposal('{"decision":"powershell","reason":"destruir"}')
        self.assertFalse(d["valid"])
        self.assertEqual(d["decision"], "defend")

    def test_respuesta_invalida_fallback(self):
        d = agents.validate_proposal("no json")
        self.assertFalse(d["valid"])

    def test_simulacion_nunca_ejecuta(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            result = agents.main(["--agente", "Tyran"])
        self.assertEqual(result, 0)
        record = json.loads(out.getvalue())
        self.assertFalse(record["executed_in_game"])
        self.assertEqual(record["source"], "simulacion")


if __name__ == "__main__":
    unittest.main()
