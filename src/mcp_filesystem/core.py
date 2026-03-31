"""Shared filesystem tool logic for both the stdio MCP server and the in-process bridge."""

from __future__ import annotations

import os
from pathlib import Path


def get_root() -> Path:
    raw = os.environ.get("AAL_FS_ROOT", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return Path.cwd().resolve()


def safe_join(root: Path, relative: str) -> Path:
    rel = (relative or ".").replace("\\", "/").lstrip("/")
    if rel == "" or rel == ".":
        target = root
    else:
        target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("Path escapes sandbox root") from exc
    return target


def list_directory_impl(relative_path: str = ".") -> str:
    root = get_root()
    p = safe_join(root, relative_path)
    if not p.exists():
        return f"Error: path does not exist: {relative_path!r}"
    if not p.is_dir():
        return f"Error: not a directory: {relative_path!r}"
    lines: list[str] = []
    for child in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        kind = "dir" if child.is_dir() else "file"
        lines.append(f"{kind}\t{child.name}")
    return "\n".join(lines) if lines else "(empty directory)"


def read_text_file_impl(relative_path: str, max_bytes: int = 200_000) -> str:
    root = get_root()
    p = safe_join(root, relative_path)
    if not p.is_file():
        return f"Error: not a file: {relative_path!r}"
    data = p.read_bytes()
    truncated = len(data) > max_bytes
    chunk = data[:max_bytes]
    text = chunk.decode("utf-8", errors="replace")
    if truncated:
        return text + f"\n\n[truncated at {max_bytes} bytes]"
    return text
