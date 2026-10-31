"""Pruebas de retrocompatibilidad lógica sin recursos propietarios."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from family_lite import (FamilyError, project_combat_event, read_family,
                         resolve_visual, safe_asset, validate_edition)

ITEM = ROOT / "data/items/katana.level5.family.json"
LITE = ROOT / "data/editions/lite.family.json"
STANDARD = ROOT / "data/editions/standard.future.family.json"
ULTIMATE = ROOT / "data/editions/ultimate.future.family.json"


class FamilyLiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.item = read_family(ITEM)
        cls.lite = read_family(LITE)

    def test_same_object_two_generations(self):
        one = resolve_visual(self.item, self.lite, "1.0")
        two = resolve_visual(self.item, self.lite, "2.0")
        self.assertEqual(one["entity_id"], two["entity_id"])
        self.assertNotEqual(one["model"], two["model"])
        self.assertNotEqual(one["effect"], two["effect"])

    def test_lite_cap_is_60(self):
        appearance = resolve_visual(self.item, self.lite, "1.0")
        self.assertEqual(appearance["max_fps"], 60)

    def test_lite_rejects_3_0(self):
        with self.assertRaises(FamilyError):
            resolve_visual(self.item, self.lite, "3.0")

    def test_future_editions_not_enabled(self):
        for path, cap, last in ((STANDARD, 300, "5.0"), (ULTIMATE, 1200, "11.0")):
            with self.subTest(path=path):
                edition = read_family(path)
                validate_edition(edition)
                self.assertFalse(edition["enabled"])
                self.assertEqual(edition["max_fps"], cap)
                self.assertIn(last, edition["generations"])
                with self.assertRaises(FamilyError):
                    resolve_visual(self.item, edition, "1.0")

    def test_server_damage_is_unchanged(self):
        event = {"type": "combat.hit", "entity_id": "weapon.katana.level5",
                 "target_id": "monster.demo.001", "damage": 25, "server_tick": 20}
        a = project_combat_event(event, resolve_visual(self.item, self.lite, "1.0"))
        b = project_combat_event(event, resolve_visual(self.item, self.lite, "2.0"))
        self.assertEqual(a["event"], b["event"])
        self.assertEqual(a["event"]["damage"], 25)

    def test_rejects_wrong_event_object(self):
        visual = resolve_visual(self.item, self.lite, "1.0")
        with self.assertRaises(FamilyError):
            project_combat_event({"type": "combat.hit", "entity_id": "another",
                                  "damage": 25}, visual)

    def test_missing_visual_uses_fallback(self):
        altered = {**self.item, "visuals": {"1.0": self.item["visuals"]["1.0"]}}
        resolved = resolve_visual(altered, self.lite, "2.0")
        self.assertEqual(resolved["model"], "concept/katana_basic")

    def test_rejects_unsafe_resource_paths(self):
        for value in ("../secret", "/root/file", "x/../secret",
                      "https://example.com/resource", r"C:\\Windows\\bad"):
            with self.subTest(value=value):
                with self.assertRaises(FamilyError):
                    safe_asset(value)

    def test_rejects_invalid_format(self):
        import json
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.family.json"
            path.write_text(json.dumps({"format": "other/1"}), encoding="utf-8")
            with self.assertRaises(FamilyError):
                read_family(path)


if __name__ == "__main__":
    unittest.main()
