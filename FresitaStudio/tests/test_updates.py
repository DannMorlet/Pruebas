"""Pruebas offline de preferencias y comparación de actualizaciones."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fresita_updates as updates

class UpdateTests(unittest.TestCase):
    def test_primera_apertura_busca_sin_instalar(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(updates.load_settings(tmp), {"buscar_al_abrir": True})
            self.assertFalse(updates.settings_path(tmp).exists())

    def test_preferencia_se_guarda_y_recupera(self):
        with tempfile.TemporaryDirectory() as tmp:
            updates.save_settings(False, tmp)
            self.assertFalse(updates.load_settings(tmp)["buscar_al_abrir"])
            updates.save_settings(True, tmp)
            self.assertTrue(updates.load_settings(tmp)["buscar_al_abrir"])

    def test_archivo_danado_usa_preferencia_segura(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=updates.settings_path(tmp)
            path.parent.mkdir(parents=True)
            path.write_text("{error",encoding="utf-8")
            self.assertTrue(updates.load_settings(tmp)["buscar_al_abrir"])

    def test_no_acepta_textos_como_booleanos(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                updates.save_settings("false",tmp)
            path=updates.settings_path(tmp)
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps({"buscar_al_abrir":"false"}),encoding="utf-8")
            self.assertTrue(updates.load_settings(tmp)["buscar_al_abrir"])

    def test_nueva_version(self):
        self.assertIn("Actualización disponible",
                      updates.update_message("b12048","b12060"))

    def test_sin_instalar(self):
        self.assertIn("no instalado",updates.update_message(None,"b12048"))

    def test_al_dia(self):
        self.assertIn("al día",updates.update_message("b12048","b12048"))

    def test_local_mas_nuevo(self):
        self.assertIn("más reciente",updates.update_message("b12049","b12048"))

    def test_rechaza_versiones_incorrectas(self):
        for tag in ("../b1", "v0.8.0", "b", "b1/"):
            with self.subTest(tag=tag),self.assertRaises(ValueError):
                updates.update_message("b12048",tag)

    def test_instalacion_automatica_configurable(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(updates.load_auto_install(tmp))
            updates.save_auto_install(False,tmp)
            self.assertFalse(updates.load_auto_install(tmp))
            updates.save_settings(False,tmp)
            self.assertFalse(updates.load_auto_install(tmp))
            self.assertFalse(updates.load_settings(tmp)["buscar_al_abrir"])
            updates.save_auto_install(True,tmp)
            self.assertTrue(updates.load_auto_install(tmp))
