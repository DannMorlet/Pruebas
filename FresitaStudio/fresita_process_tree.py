"""Inspección informativa de posibles procesos secundarios en Windows.

No lee argumentos, rutas, memoria ni contenidos de los procesos. Una relación
padre-hijo observada en una instantánea NO demuestra qué proceso carga la IA.
"""
from __future__ import annotations

import ctypes
import os


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
