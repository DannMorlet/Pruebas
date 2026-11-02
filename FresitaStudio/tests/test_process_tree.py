"""Parentesco de procesos: solo candidatos, sin atribución de memoria."""
import os
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_process_tree import possible_descendants, discover_possible_children, windows_process_pairs, candidate_ram_snapshot, candidate_gpu_snapshot


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

    def test_ram_candidatos_separados_sin_suma(self):
        rows = candidate_ram_snapshot([10, 20, 30], probe=lambda pid: {10: 120, 20: 400, 30: 0}[pid])
        self.assertEqual(rows, [(10, 120), (20, 400), (30, 0)])

    def test_ram_denegada_no_se_inventa(self):
        def denied(_pid):
            raise PermissionError("Acceso denegado")
        self.assertEqual(candidate_ram_snapshot([10], probe=denied), [(10, None)])

    def test_ram_invalida_no_se_presenta(self):
        for invalid in (True, -1, 2.5, "500", float("nan")):
            self.assertEqual(candidate_ram_snapshot([10], probe=lambda _pid: invalid), [(10, None)])

    def test_pids_invalidos_y_duplicados(self):
        for bad in ([0], [True], [10, 10], [4294967296], ["10"], list(range(1, 35))):
            with self.assertRaises(ValueError):
                candidate_ram_snapshot(bad, probe=lambda _pid: 1)

    def test_lista_vacia(self):
        self.assertEqual(candidate_ram_snapshot([], probe=lambda _pid: 100), [])

    def test_ram_consulta_solo_pids_solicitados(self):
        seen = []
        def probe(pid):
            seen.append(pid)
            return 5
        self.assertEqual(candidate_ram_snapshot([3, 9], probe=probe), [(3, 5), (9, 5)])
        self.assertEqual(seen, [3, 9])


    def test_vram_candidatos_una_consulta_sin_suma(self):
        calls = []
        def runner():
            calls.append(True)
            return "10, 512\n20, 128\n99, 999\n"
        self.assertEqual(candidate_gpu_snapshot([10, 20, 30], runner=runner),
                         [(10, 512), (20, 128), (30, None)])
        self.assertEqual(len(calls), 1)

    def test_vram_wddm_y_duplicados_son_nd(self):
        output = "10, N/A\n20, 300\n20, 250\n"
        self.assertEqual(candidate_gpu_snapshot([10, 20], runner=lambda: output),
                         [(10, None), (20, None)])

    def test_vram_error_de_nvidia_smi_es_nd(self):
        def denied():
            raise OSError("Sin acceso a NVIDIA")
        self.assertEqual(candidate_gpu_snapshot([10, 20], runner=denied),
                         [(10, None), (20, None)])

    def test_vram_salida_invalida_no_se_inventa(self):
        self.assertEqual(candidate_gpu_snapshot([10], runner=lambda: None),
                         [(10, None)])
        self.assertEqual(candidate_gpu_snapshot([10], runner=lambda: "10, 512 MiB\n"),
                         [(10, None)])

    def test_vram_lista_invalida_o_duplicada(self):
        for bad in ([0], [True], [10, 10], ["10"], [4294967296],
                    list(range(1, 35))):
            with self.subTest(pids=bad), self.assertRaises(ValueError):
                candidate_gpu_snapshot(bad, runner=lambda: "")

    def test_vram_lista_vacia_no_consulta(self):
        def should_not_run():
            raise AssertionError("No debe ejecutar nvidia-smi")
        self.assertEqual(candidate_gpu_snapshot([], runner=should_not_run), [])

    @unittest.skipUnless(os.name == "nt", "Toolhelp requiere Windows")
    def test_snapshot_real_solo_lectura(self):
        rows = windows_process_pairs()
        self.assertIsNotNone(rows)
        self.assertTrue(any(pid == os.getpid() for pid, _ in rows))


if __name__ == "__main__":
    unittest.main()
