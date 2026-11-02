"""Detección conservadora del PID que escucha en el puerto HTTP local (Windows)."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

from fresita_predict import local_server


def parse_listening_pids(output: str, port: int) -> list[int]:
    """PIDs únicos de listeners IPv4 en 127.0.0.1 o 0.0.0.0, nunca conexiones activas."""
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("Puerto inválido")
    pids = set()
    for line in output.splitlines():
        columns = line.split()
        if len(columns) != 5 or columns[0].upper() != "TCP":
            continue
        if columns[3].upper() not in ("LISTENING", "ESCUCHANDO"):
            continue
        address, sep, local_port = columns[1].rpartition(":")
        if (not sep or address not in ("127.0.0.1", "0.0.0.0")
                or not local_port.isascii() or not local_port.isdecimal()
                or int(local_port) != port):
            continue
        pid = columns[4]
        if pid.isascii() and pid.isdecimal() and 1 <= int(pid) <= 4294967295:
            pids.add(int(pid))
    return sorted(pids)


def discover_server_pid(endpoint: str, *, runner=None, windows=None) -> int | None:
    """Devuelve PID sólo con un listener inequívoco; no inicia ni toca procesos."""
    _, port = local_server(endpoint)
    if windows is None:
        windows = os.name == "nt"
    if not windows:
        return None
    if runner is None:
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        executable = Path(system_root) / "System32" / "netstat.exe"
        command = str(executable) if executable.is_file() else shutil.which("netstat")
        if not command:
            return None
        runner = lambda: subprocess.run(
            [command, "-ano", "-p", "tcp"], capture_output=True, text=True,
            errors="replace", timeout=5, check=True).stdout
    try:
        pids = parse_listening_pids(runner(), port)
    except (OSError, subprocess.SubprocessError, ValueError, TypeError):
        return None
    return pids[0] if len(pids) == 1 else None
