"""Path helpers — no longer spawns AalMcp.exe subprocess."""

from __future__ import annotations

import sys
from pathlib import Path


def bundle_dir() -> Path:
    """Directory containing the main executable (frozen) or project src (dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent
