"""Resolve bundled resources when running under PyInstaller."""

from __future__ import annotations

import sys
from pathlib import Path


def bundle_dir() -> Path:
    """Directory containing the main executable (frozen) or project src (dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def fs_mcp_executable() -> Path | None:
    """OmniFsMcp.exe next to the main app (preferred after packaging)."""
    exe = bundle_dir() / "OmniFsMcp.exe"
    if exe.is_file():
        return exe
    return None
