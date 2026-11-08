"""Detección del PID de un servidor local, sin abrir puertos ni procesos."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fresita_pid import discover_server_pid, parse_listening_pids


class ServerPidTests(unittest.TestCase):
    def test_listener_exacto(self):
        output = """TCP    127.0.0.1:1234    0.0.0.0:0    LISTENING    4567
TCP    127.0.0.1:1235    0.0.0.0:0    LISTENING    9876
TCP    127.0.0.1:1234    127.0.0.1:5555    ESTABLISHED    2222
"""
        self.assertEqual(parse_listening_pids(output, 1234), [4567])

    def test_wildcard_y_estado_espanol(self):
        self.assertEqual(parse_listening_pids(
            "  TCP  0.0.0.0:1234  0.0.0.0:0  ESCUCHANDO  100\n", 1234), [100])

    def test_ignora_direccion_no_alcanzable_y_tcp6(self):
        output = """TCP 192.168.1.5:1234 0.0.0.0:0 LISTENING 10
TCP [::]:1234 [::]:0 LISTENING 11
TCP 127.0.0.2:1234 0.0.0.0:0 LISTENING 12
"""
        self.assertEqual(parse_listening_pids(output, 1234), [])

    def test_dos_listeners_distintos_no_adivina(self):
        output = """TCP 127.0.0.1:1234 0.0.0.0:0 LISTENING 100
TCP 0.0.0.0:1234 0.0.0.0:0 LISTENING 200
"""
        self.assertIsNone(discover_server_pid(
            "http://127.0.0.1:1234/v1", windows=True, runner=lambda: output))

    def test_filas_duplicadas_mismo_pid(self):
        output = """TCP 127.0.0.1:1234 0.0.0.0:0 LISTENING 100
TCP 127.0.0.1:1234 0.0.0.0:0 LISTENING 100
"""
        self.assertEqual(discover_server_pid(
            "http://127.0.0.1:1234/v1", windows=True, runner=lambda: output), 100)

    def test_pid_invalido_y_puerto_exacto(self):
        output = """TCP 127.0.0.1:1234 0.0.0.0:0 LISTENING 0
TCP 127.0.0.1:1234 0.0.0.0:0 LISTENING N/A
TCP 127.0.0.1:12340 0.0.0.0:0 LISTENING 123
"""
        self.assertEqual(parse_listening_pids(output, 1234), [])

    def test_no_windows_y_error_son_nd(self):
        endpoint = "http://127.0.0.1:1234/v1"
        self.assertIsNone(discover_server_pid(endpoint, windows=False,
            runner=lambda: self.fail("No ejecutar netstat fuera de Windows")))
        self.assertIsNone(discover_server_pid(endpoint, windows=True,
            runner=lambda: (_ for _ in ()).throw(OSError("sin acceso"))))

    def test_endpoint_remoto_rechazado(self):
        with self.assertRaises(ValueError):
            discover_server_pid("http://example.com:1234/v1", windows=True,
                runner=lambda: "")


if __name__ == "__main__":
    unittest.main()
