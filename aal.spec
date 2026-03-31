# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

_spec_dir = Path(os.environ.get("SPECPATH", os.getcwd())).resolve()
src = str(_spec_dir / "src")

# Entry is package __main__: PyInstaller sometimes omits sibling submodules from the
# graph; force-include the whole omni tree and mcp_filesystem (used by omni.mcp_bridge).
hidden_omni = [
    "omni",
    "omni.app",
    "omni.chat_pipeline",
    "omni.mcp_bridge",
    "omni.ollama_chat",
    "omni.paths",
]

hidden_mcp_fs = [
    "mcp_filesystem",
    "mcp_filesystem.core",
]

# mcp.cli imports typer and sys.exits if missing — do not use collect_submodules("mcp").
hidden_mcp = [
    "mcp.server",
    "mcp.types",
    "mcp.server.stdio",
]

a = Analysis(
    [str(Path(src) / "omni" / "__main__.py")],
    pathex=[src],
    binaries=[],
    datas=[],
    hiddenimports=hidden_mcp + hidden_omni + hidden_mcp_fs,
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
