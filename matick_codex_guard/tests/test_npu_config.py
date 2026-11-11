import tempfile
import unittest
from pathlib import Path

from matick_codex_guard.npu_config import NPUSupervisorConfig, npu_label, require_npu_device


class NpuIsolationTests(unittest.TestCase):
    def test_visible_tag_is_required_once(self):
        self.assertEqual(npu_label("Supervisor"), "Supervisor (NPU)")
        self.assertEqual(npu_label("Supervisor (NPU)"), "Supervisor (NPU)")
        with self.assertRaises(ValueError):
            npu_label("")

    def test_reject_every_fallback_device(self):
        for device in ("CPU", "GPU", "AUTO", "MULTI", "NPU,CPU", "npu", ""):
            with self.subTest(device=device), self.assertRaises(RuntimeError):
                require_npu_device(device)
        require_npu_device("NPU")

    def test_paths_are_exclusive_and_no_side_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "npu"
            config = NPUSupervisorConfig(root)
            self.assertEqual(config.section("rag"), root / "rag")
            self.assertEqual(config.section("historial"), root / "historial")
            self.assertFalse(root.exists())
            self.assertFalse(config.as_manifest()["runtime_verified"])
            with self.assertRaises(ValueError):
                config.section("../cpu")

    def test_reject_fallback_and_other_roots(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                NPUSupervisorConfig(Path(tmp) / "cpu")
            with self.assertRaises(ValueError):
                NPUSupervisorConfig(Path(tmp) / "npu", allow_fallback=True)
            with self.assertRaises(RuntimeError):
                NPUSupervisorConfig(Path(tmp) / "npu", device="CPU")


if __name__ == "__main__":
    unittest.main()
