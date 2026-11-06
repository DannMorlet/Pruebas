"""Inspección informativa de posibles procesos secundarios en Windows.

No lee argumentos, rutas, memoria ni contenidos de los procesos. Una relación
padre-hijo observada en una instantánea NO demuestra qué proceso carga la IA.
"""
from __future__ import annotations

import ctypes
import os
import shutil
import subprocess


def possible_descendants(pairs, root_pid: int, *, max_depth: int = 3, limit: int = 32) -> list[int] | None:
    """Devuelve candidatos por parentesco (BFS); None si el árbol es ambiguo/excesivo."""
    if type(root_pid) is not int or not 1 <= root_pid <= 4294967295:
        raise ValueError("PID inválido")
    if type(max_depth) is not int or not 1 <= max_depth <= 8:
        raise ValueError("Profundidad inválida")
    if type(limit) is not int or not 1 <= limit <= 256:
        raise ValueError("Límite inválido")
    children: dict[int, set[int]] = {}
    for pid, parent in pairs:
        if (type(pid) is int and type(parent) is int and
                1 <= pid <= 4294967295 and 0 <= parent <= 4294967295 and
                pid != parent):
            children.setdefault(parent, set()).add(pid)
    seen = {root_pid}
    frontier = [root_pid]
    found = []
    for _ in range(max_depth):
        next_frontier = []
        for parent in frontier:
            for child in sorted(children.get(parent, ())):
                if child in seen:
                    continue
                seen.add(child)
                found.append(child)
                next_frontier.append(child)
                if len(found) > limit:
                    return None  # no presentar un árbol parcial como completo
        frontier = next_frontier
        if not frontier:
            break
    return found


def candidate_ram_snapshot(pids, *, probe=None) -> list[tuple[int, int | None]]:
    """RAM residente por PID observado; no atribuye memoria al modelo.

    No suma procesos; N/D si Windows deniega la consulta.
    """
    if (not isinstance(pids, (list, tuple)) or len(pids) > 33
            or any(type(pid) is not int or not 1 <= pid <= 4294967295 for pid in pids)
            or len(set(pids)) != len(pids)):
        raise ValueError("Lista de PIDs inválida o duplicada")
    if probe is None:
        from fresita_resources import probe_process_ram
        probe = probe_process_ram
    result = []
    for pid in pids:
        try:
            mib = probe(pid)
        except (OSError, ValueError):
            mib = None
        result.append((pid, mib if type(mib) is int and mib >= 0 else None))
    return result



def candidate_gpu_snapshot(pids, *, runner=None) -> list[tuple[int, int | None]]:
    """VRAM observada por PID candidato, en GPU 0; no suma ni atribuye al modelo.

    Consulta nvidia-smi una sola vez. WDDM puede devolver N/A, que se muestra
    como N/D. Los PIDs son candidatos por parentesco, no motores verificados.
    """
    if (not isinstance(pids, (list, tuple)) or len(pids) > 33
            or any(type(pid) is not int or not 1 <= pid <= 4294967295 for pid in pids)
            or len(set(pids)) != len(pids)):
        raise ValueError("Lista de PIDs inválida o duplicada")
    if not pids:
        return []
    unavailable = [(pid, None) for pid in pids]
    if runner is None:
        executable = shutil.which("nvidia-smi")
        if not executable:
            return unavailable
        def runner():
            return subprocess.run(
                [executable, "--id=0", "--query-compute-apps=pid,used_gpu_memory",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3, check=True).stdout
    try:
        output = runner()
        if not isinstance(output, str):
            return unavailable
        from fresita_resources import parse_process_gpu_memory
        return [(pid, parse_process_gpu_memory(output, pid)) for pid in pids]
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        return unavailable



def candidate_gpu_evidence_snapshot(pids, *, runner=None) -> list[tuple[int, bool | None, int | None]]:
    """Evidencia puntual de PID en lista de cómputo NVIDIA GPU 0.

    True indica una fila inequívoca de nvidia-smi, NO que el PID aloje
    el modelo. None significa no confirmado (ausente, WDDM o error).
    La VRAM puede ser N/D aun cuando se observe el PID.
    """
    if (not isinstance(pids, (list, tuple)) or len(pids) > 33
            or any(type(pid) is not int or not 1 <= pid <= 4294967295 for pid in pids)
            or len(set(pids)) != len(pids)):
        raise ValueError("Lista de PIDs inválida o duplicada")
    if not pids:
        return []
    unavailable = [(pid, None, None) for pid in pids]
    if runner is None:
        executable = shutil.which("nvidia-smi")
        if not executable:
            return unavailable
        def runner():
            return subprocess.run(
                [executable, "--id=0", "--query-compute-apps=pid,used_gpu_memory",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3, check=True).stdout
    try:
        output = runner()
        if not isinstance(output, str):
            return unavailable
        from fresita_resources import parse_process_gpu_memory
        rows = {}
        for line in output.splitlines():
            parts = [part.strip() for part in line.split(",")]
            if (len(parts) == 2 and parts[0].isascii() and parts[0].isdecimal()
                    and 1 <= int(parts[0]) <= 4294967295):
                rows.setdefault(int(parts[0]), []).append(parts[1])
        result = []
        for pid in pids:
            if len(rows.get(pid, [])) != 1:
                result.append((pid, None, None))
            else:
                result.append((pid, True, parse_process_gpu_memory(output, pid)))
        return result
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        return unavailable


def windows_process_pairs() -> list[tuple[int, int]] | None:
    """Snapshot Toolhelp de PID/PPID solamente; N/D si Windows no permite leer."""
    if os.name != "nt":
        return None
    try:
        from ctypes import wintypes

        class ProcessEntry(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", wintypes.LONG),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", wintypes.WCHAR * 260),
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
        kernel.Process32FirstW.restype = wintypes.BOOL
        kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
        kernel.Process32NextW.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        handle = kernel.CreateToolhelp32Snapshot(0x00000002, 0)
        if handle is None or handle == ctypes.c_void_p(-1).value:
            return None
        try:
            entry = ProcessEntry()
            entry.dwSize = ctypes.sizeof(entry)
            if not kernel.Process32FirstW(handle, ctypes.byref(entry)):
                return None
            rows = []
            while True:
                rows.append((int(entry.th32ProcessID), int(entry.th32ParentProcessID)))
                if not kernel.Process32NextW(handle, ctypes.byref(entry)):
                    break
            return rows
        finally:
            kernel.CloseHandle(handle)
    except (AttributeError, OSError, ValueError):
        return None


def discover_possible_children(pid: int, *, snapshot=None, windows=None) -> list[int] | None:
    """Posibles hijos, no procesos de IA verificados; no suma su RAM/VRAM."""
    if type(pid) is not int or not 1 <= pid <= 4294967295:
        raise ValueError("PID inválido")
    if windows is None:
        windows = os.name == "nt"
    if not windows:
        return None
    rows = snapshot() if snapshot is not None else windows_process_pairs()
    if rows is None:
        return None
    return possible_descendants(rows, pid)
