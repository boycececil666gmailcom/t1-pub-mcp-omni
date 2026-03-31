# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

_spec_dir = Path(os.environ.get("SPECPATH", os.getcwd())).resolve()
src = str(_spec_dir / "src")

# ── MCP: only collect the submodules the bridge / server actually need.
hidden_mcp = [
    m for m in collect_submodules("mcp")
    if not m.startswith("mcp.cli")
]

a = Analysis(
    [str(Path(src) / "omni" / "__main__.py")],
    pathex=[src],
    binaries=[],
    datas=[],
    hiddenimports=hidden_mcp,
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
    name="AAL",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
