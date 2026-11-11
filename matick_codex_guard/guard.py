"""Matick Codex: verificación reproducible y memoria de fallos (stdlib)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

MAX_LOG = 5000


def checked_workspace(folder: str | Path) -> Path:
    """Rechaza raíces y directorios Windows sensibles; no es sandbox de procesos."""
    target = Path(folder).expanduser().resolve(strict=True)
    if not target.is_dir() or target == Path(target.anchor):
        raise ValueError("Selecciona una carpeta de proyecto, nunca una unidad raíz")
    if os.name == "nt":
        blocked = [os.environ.get("SystemRoot", r"C:\Windows"),
                   os.environ.get("ProgramFiles", r"C:\Program Files"),
                   os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                   os.environ.get("ProgramData", r"C:\ProgramData")]
        for item in blocked:
            root = Path(item).resolve(strict=False)
            if target == root or root in target.parents or target in root.parents:
                raise ValueError(f"Carpeta protegida: {root}")
    return target


def checked_child(root: Path, relative: str) -> Path:
    child = (root / relative).resolve(strict=True)
    if child != root and root not in child.parents:
        raise ValueError("Ruta fuera del proyecto")
    if not child.is_dir():
        raise ValueError("La ruta de pruebas debe ser una carpeta")
    return child


def fingerprint(message: str) -> str:
    normalized = re.sub(r"\s+", " ", message.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


class Guard:
    def __init__(self, workspace: str | Path, db: str | Path | None = None):
        self.workspace = checked_workspace(workspace)
        path = Path(db).expanduser() if db else Path.home() / ".matick_codex_guard" / "history.sqlite3"
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workspace TEXT NOT NULL, issue TEXT NOT NULL, model TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('failed','verified')),
            fingerprint TEXT NOT NULL, detail TEXT NOT NULL,
            created_at TEXT NOT NULL)""")
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def _record(self, issue: str, status: str, detail: str, model: str) -> dict:
        if not issue.strip():
            raise ValueError("Falta identificador del error")
        clipped = detail[-MAX_LOG:]
        with self.conn:
            self.conn.execute("""INSERT INTO attempts
                (workspace, issue, model, status, fingerprint, detail, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (str(self.workspace), issue, model, status, fingerprint(clipped),
                 clipped, datetime.now(timezone.utc).isoformat()))
        return self.status(issue)

    def failure(self, issue: str, detail: str, model: str = "Sol") -> dict:
        return self._record(issue, "failed", detail, model)

    def status(self, issue: str) -> dict:
        rows = self.conn.execute("""SELECT status, fingerprint, model, detail
            FROM attempts WHERE workspace=? AND issue=? ORDER BY id DESC""",
            (str(self.workspace), issue)).fetchall()
        # La verificación satisfactoria reinicia el contador para este error.
        recent = []
        for row in rows:
            if row[0] == "verified":
                break
            recent.append(row)
        repeated = len(recent) >= 2 and recent[0][1] == recent[1][1]
        escalate = len(recent) >= 3 or repeated
        return {
            "issue": issue,
            "last_status": rows[0][0] if rows else "sin_registro",
            "consecutive_failures": len(recent),
            "repeated_error": repeated,
            "recommend_astra": escalate,
            "astra_activated": False,  # Nunca se llama a un modelo desde este módulo.
            "reason": "Tres fallos o error repetido" if escalate else "Continuar con modelo económico",
        }

    def verify(self, issue: str, tests_dir: str = "tests", timeout: int = 90,
               model: str = "Sol") -> dict:
        tests = checked_child(self.workspace, tests_dir)
        if not any(tests.rglob("test*.py")):
            return self.failure(issue, "Sin archivos test*.py: verificación no realizada", model)
        # Sin shell, instalación, escritura en zonas del sistema ni cambios de modelo.
        argv = [sys.executable, "-m", "unittest", "discover", "-s", str(tests), "-p", "test*.py", "-v"]
        try:
            result = subprocess.run(argv, cwd=self.workspace, capture_output=True,
                                    text=True, timeout=timeout, shell=False, check=False)
            detail = f"exit={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            passed = result.returncode == 0 and "Ran 0 tests" not in detail
        except subprocess.TimeoutExpired:
            detail = f"timeout de {timeout}s al ejecutar pruebas"
            passed = False
        if passed:
            return self._record(issue, "verified", detail, model)
        return self.failure(issue, detail, model)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Matick Codex: memoria y verificación sin autoescalar")
    parser.add_argument("action", choices=("failure", "verify", "status"))
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--issue", required=True)
    parser.add_argument("--error", default="")
    parser.add_argument("--tests-dir", default="tests")
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args(argv)
    if args.timeout < 1 or args.timeout > 600:
        parser.error("timeout entre 1 y 600 segundos")
    guard = Guard(args.workspace)
    try:
        if args.action == "failure":
            result = guard.failure(args.issue, args.error)
        elif args.action == "verify":
            result = guard.verify(args.issue, args.tests_dir, args.timeout)
        else:
            result = guard.status(args.issue)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if args.action == "verify" and result["last_status"] != "verified" else 0
    finally:
        guard.close()


if __name__ == "__main__":
    sys.exit(main())
