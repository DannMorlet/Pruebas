"""Muestreo puntual durante un benchmark, sin sondeo permanente ni dependencias ML."""
from __future__ import annotations

import ctypes
import math
import os
import shutil
import subprocess
import threading


def parse_process_gpu_memory(output, pid):
    """VRAM MiB de un PID en GPU 0, sólo si nvidia-smi devuelve una fila inequívoca."""
    if type(pid) is not int or pid <= 0:
        raise ValueError("PID inválido")
    matches = []
    for line in output.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 2 or not parts[0].isdigit() or int(parts[0]) != pid:
            continue
        if not parts[1].isdigit():
            return None  # WDDM suele informar N/A: no inferir VRAM
        matches.append(int(parts[1]))
    return matches[0] if len(matches) == 1 else None


def probe_resources(pid=None):
    """Memoria global y, opcionalmente, VRAM del proceso PID en GPU 0."""
    if pid is not None and (type(pid) is not int or pid <= 0):
        raise ValueError("PID inválido")
    result = {"gpu_used_mib": None, "gpu_total_mib": None,
              "ram_used_mib": None, "ram_total_mib": None,
              "gpu_process_used_mib": None}
    exe = shutil.which("nvidia-smi")
    if exe:
        try:
            out = subprocess.run(
                [exe, "--query-gpu=memory.used,memory.total",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3, check=True
            ).stdout.strip().splitlines()
            if out:
                used, total = (int(x.strip()) for x in out[0].split(",")[:2])
                if 0 <= used <= total and total > 0:
                    result["gpu_used_mib"], result["gpu_total_mib"] = used, total
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    if exe and pid is not None:
        try:
            out = subprocess.run(
                [exe, "--id=0", "--query-compute-apps=pid,used_gpu_memory",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3, check=True
            ).stdout
            used = parse_process_gpu_memory(out, pid)
            if used is not None and (result["gpu_total_mib"] is None
                                     or used <= result["gpu_total_mib"]):
                result["gpu_process_used_mib"] = used
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    if os.name == "nt":
        try:
            class MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            state = MemoryStatus()
            state.dwLength = ctypes.sizeof(state)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)):
                mib = 1024 * 1024
                result["ram_total_mib"] = state.ullTotalPhys // mib
                result["ram_used_mib"] = (state.ullTotalPhys - state.ullAvailPhys) // mib
        except (AttributeError, OSError, ValueError):
            pass
    return result


class ResourceSampler:
    """Captura línea base, pico y última muestra sólo durante el benchmark."""

    def __init__(self, *, probe=None, interval=0.75, pid=None):
        if not isinstance(interval, (int, float)) or isinstance(interval, bool) or not math.isfinite(interval) or interval < 0.1:
            raise ValueError("Intervalo de muestreo inválido")
        if pid is not None and (type(pid) is not int or pid <= 0):
            raise ValueError("PID inválido")
        self.pid = pid
        self.probe = probe if probe is not None else lambda: probe_resources(pid=pid)
        self.interval = interval
        self.samples = {"gpu": [], "ram": [], "gpu_process": []}
        self.totals = {"gpu": None, "ram": None}
        self._stop = threading.Event()
        self._thread = None
        self._lock = threading.Lock()

    def capture(self):
        try:
            data = self.probe()
        except (OSError, ValueError, subprocess.SubprocessError):
            return
        if not isinstance(data, dict):
            return
        with self._lock:
            for kind in ("gpu", "ram"):
                used, total = data.get(kind + "_used_mib"), data.get(kind + "_total_mib")
                if (type(used) is int and type(total) is int
                        and 0 <= used <= total and total > 0):
                    self.samples[kind].append(used)
                    self.totals[kind] = total
            process_used = data.get("gpu_process_used_mib")
            if (self.pid is not None and type(process_used) is int
                    and 0 <= process_used
                    and (self.totals["gpu"] is None
                         or process_used <= self.totals["gpu"])):
                self.samples["gpu_process"].append(process_used)

    def start(self):
        if self._thread is not None:
            raise RuntimeError("Muestreo ya iniciado")
        self.capture()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def _loop(self):
        while not self._stop.wait(self.interval):
            self.capture()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=4)
        return self.summary()

    def summary(self):
        report = {}
        with self._lock:
            for kind in ("gpu", "ram"):
                values = list(self.samples[kind])
                prefix = kind + "_global"
                report[prefix + "_muestras"] = len(values)
                report[prefix + "_base_mib"] = values[0] if values else None
                report[prefix + "_pico_mib"] = max(values) if values else None
                report[prefix + "_final_mib"] = values[-1] if values else None
                report[prefix + "_total_mib"] = self.totals[kind] if values else None
                report[prefix + "_delta_pico_base_mib"] = max(values) - values[0] if values else None
            values = list(self.samples["gpu_process"])
            report["gpu_proceso_pid"] = self.pid
            report["gpu_proceso_muestras"] = len(values)
            report["gpu_proceso_base_mib"] = values[0] if values else None
            report["gpu_proceso_pico_mib"] = max(values) if values else None
            report["gpu_proceso_final_mib"] = values[-1] if values else None
            report["gpu_proceso_delta_pico_base_mib"] = (
                max(values) - values[0] if values else None)
        report["advertencia_recursos"] = (
            "VRAM de GPU 0 y RAM globales, no atribuibles al modelo. "
            "El muestreo puede omitir picos entre lecturas; "
            "N/D si no hay nvidia-smi o medición disponible. "
            "La VRAM por PID (si se solicitó) incluye todo el proceso, "
            "no sólo el modelo; WDDM puede reportar N/D."
        )
        return report
