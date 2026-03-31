# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

_spec_dir = Path(os.environ.get("SPECPATH", os.getcwd())).resolve()
src = str(_spec_dir / "src")

hidden_mcp = collect_submodules("mcp", filter=lambda name: not name.startswith("mcp.cli"))

a = Analysis(
    [str(Path(src) / "mcp_filesystem" / "__main__.py")],
    pathex=[src],
    binaries=[],
    datas=[],
    hiddenimports=hidden_mcp
    + [
        "mcp.server.fastmcp",
        "mcp.server.stdio",
        "mcp_filesystem.server",
        "pydantic_settings",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AalMcp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
