"""Configuración aislada del supervisor (NPU); no incluye runtime OpenVINO."""
from dataclasses import dataclass
from pathlib import Path
import re

LABEL = "(NPU)"
SECTIONS = ("modelos", "herramientas", "rag", "historial", "configuracion")
VALID_BACKEND_DEVICE = "NPU"


def npu_label(name: str) -> str:
    """Etiqueta visible explícita; evita duplicaciones y etiquetas engañosas."""
    raw = re.sub(r"\s*\(NPU\)\s*$", "", name.strip(), flags=re.I).strip()
    if not raw:
        raise ValueError("El componente requiere un nombre")
    return f"{raw} {LABEL}"


def require_npu_device(actual: str) -> None:
    """Bloqueo de selección; NO es una medición real de ejecución del hardware."""
    if actual != VALID_BACKEND_DEVICE:
        raise RuntimeError(
            f"Supervisor (NPU): dispositivo no permitido: {actual!r}. "
            "No hay fallback automático a CPU, GPU, AUTO ni nube."
        )


@dataclass(frozen=True)
class NPUSupervisorConfig:
    root: Path
    device: str = VALID_BACKEND_DEVICE
    allow_fallback: bool = False

    def __post_init__(self):
        root = Path(self.root).expanduser().resolve(strict=False)
        if root == Path(root.anchor):
            raise ValueError("Directorio raíz de unidad no permitido")
        if root.name.lower() != "npu":
            raise ValueError("La carpeta exclusiva debe llamarse npu")
        if self.allow_fallback:
            raise ValueError("Fallback prohibido para Supervisor (NPU)")
        require_npu_device(self.device)
        object.__setattr__(self, "root", root)

    def section(self, key: str) -> Path:
        if key not in SECTIONS:
            raise ValueError("Sección no permitida; usa las áreas exclusivas (NPU)")
        return self.root / key

    def as_manifest(self) -> dict:
        """Manifest sin secretos ni estado de disponibilidad real."""
        return {
            "name": "Supervisor (NPU)",
            "device": "NPU",
            "allow_fallback": False,
            "runtime_verified": False,
            "sections": {npu_label(x.capitalize()): str(self.section(x)) for x in SECTIONS},
        }
