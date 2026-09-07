"""Application resource lookup independent of the current working directory."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
INSTALLED_RESOURCE_ROOT = Path(sys.prefix) / "share" / "hypertrophy-engine"


def resource_path(relative_path: str | Path) -> Path:
    """Return an existing application resource or raise a descriptive error."""
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("resource path must be relative and remain inside the resource directory")

    roots = [PROJECT_ROOT]
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        roots.insert(0, Path(bundle_root))
    roots.append(INSTALLED_RESOURCE_ROOT)

    for root in roots:
        candidate = root / relative
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(f"application resource not found: {relative.as_posix()}")
