import tempfile
import unittest
from pathlib import Path
from matick_codex_guard.guard import Guard, checked_child, checked_workspace


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "project"
        self.root.mkdir()
        self.db = Path(self.tmp.name) / "history.sqlite3"

    def guard(self):
        g = Guard(self.root, self.db)
        self.addCleanup(g.close)
        return g

    def test_reject_volume_root_and_escape(self):
        with self.assertRaises(ValueError):
            checked_workspace(Path(self.root.anchor))
        with self.assertRaises(ValueError):
            checked_child(self.root, "..")

    def test_persistent_record_and_three_failures(self):
        g = self.guard()
        g.failure("build", "error uno")
        g.failure("build", "error dos")
        self.assertFalse(g.status("build")["recommend_astra"])
        g.close()
        g2 = self.guard()
        result = g2.failure("build", "error tres")
        self.assertEqual(result["consecutive_failures"], 3)
        self.assertTrue(result["recommend_astra"])
        self.assertFalse(result["astra_activated"])

    def test_repeated_error_escalates_early(self):
        g = self.guard()
        g.failure("same", "FileNotFound: foo")
        result = g.failure("same", "FileNotFound: foo")
        self.assertTrue(result["repeated_error"])
        self.assertTrue(result["recommend_astra"])

    def test_no_tests_cannot_pass(self):
        (self.root / "tests").mkdir()
        result = self.guard().verify("empty")
        self.assertEqual(result["last_status"], "failed")

    def test_tests_pass_reset_failures(self):
        tests = self.root / "tests"
        tests.mkdir()
        (tests / "test_example.py").write_text("import unittest\nclass T(unittest.TestCase):\n def test_yes(self): self.assertTrue(True)\n")
        g = self.guard()
        g.failure("demo", "no compila")
        result = g.verify("demo")
        self.assertEqual(result["last_status"], "verified")
        self.assertEqual(result["consecutive_failures"], 0)

    def test_failing_tests_never_count_as_success(self):
        tests = self.root / "tests"
        tests.mkdir()
        (tests / "test_example.py").write_text("import unittest\nclass T(unittest.TestCase):\n def test_no(self): self.fail('bug')\n")
        result = self.guard().verify("demo")
        self.assertEqual(result["last_status"], "failed")


if __name__ == "__main__":
    unittest.main()
