"""Parentesco de procesos: solo candidatos, sin atribución de memoria."""
import os
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_process_tree import possible_descendants, discover_possible_children, windows_process_pairs


class ProcessTreeTests(unittest.TestCase):
    def test_descendientes_y_orden(self):
        rows = [(22, 10), (30, 22), (20, 10), (31, 30), (99, 5)]
        self.assertEqual(possible_descendants(rows, 10), [20, 22, 30, 31])

    def test_no_confundir_otros_procesos(self):
        self.assertEqual(possible_descendants([(5, 2), (6, 5)], 7), [])

    def test_ciclos_duplicados_y_raiz(self):
        rows = [(20, 10), (20, 10), (10, 20), (30, 20)]
        self.assertEqual(possible_descendants(rows, 10), [20, 30])

    def test_profundidad_limitada(self):
        rows = [(2, 1), (3, 2), (4, 3), (5, 4)]
        self.assertEqual(possible_descendants(rows, 1), [2, 3, 4])

    def test_exceso_no_muestra_arbol_incompleto(self):
        self.assertIsNone(possible_descendants([(x, 1) for x in range(2, 8)], 1, limit=3))

    def test_filas_invalidas_ignoradas(self):
        rows = [(0, 10), (-1, 10), (True, 10), (12, 12), (13, 10), (14, -1)]
        self.assertEqual(possible_descendants(rows, 10), [13])

    def test_validacion_y_sin_windows(self):
        with self.assertRaises(ValueError):
            possible_descendants([], True)
        with self.assertRaises(ValueError):
            discover_possible_children(0)
        self.assertIsNone(discover_possible_children(123, windows=False))

    def test_inyeccion_snapshot(self):
        self.assertEqual(discover_possible_children(7, windows=True,
            snapshot=lambda: [(8, 7), (9, 8)]), [8, 9])
        self.assertIsNone(discover_possible_children(7, windows=True,
            snapshot=lambda: None))

    @unittest.skipUnless(os.name == "nt", "Toolhelp requiere Windows")
    def test_snapshot_real_solo_lectura(self):
        rows = windows_process_pairs()
        self.assertIsNotNone(rows)
        self.assertTrue(any(pid == os.getpid() for pid, _ in rows))


if __name__ == "__main__":
    unittest.main()
