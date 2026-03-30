"""Sandboxed filesystem tools exposed via MCP (stdio)."""

from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "omni-filesystem",
    instructions=(
        "Filesystem tools restricted to OMNI_FS_ROOT (or the process working directory). "
        "Paths are relative to that root. Listing and reading text files only."
    ),
)


def _root() -> Path:
    raw = os.environ.get("OMNI_FS_ROOT", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return Path.cwd().resolve()


def _safe_join(relative: str) -> Path:
    root = _root()
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


@mcp.tool()
def list_directory(relative_path: str = ".") -> str:
    """List files and subdirectories under the sandbox root."""
    p = _safe_join(relative_path)
    if not p.exists():
        return f"Error: path does not exist: {relative_path!r}"
    if not p.is_dir():
        return f"Error: not a directory: {relative_path!r}"
    lines: list[str] = []
    for child in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        kind = "dir" if child.is_dir() else "file"
        lines.append(f"{kind}\t{child.name}")
    return "\n".join(lines) if lines else "(empty directory)"


@mcp.tool()
def read_text_file(relative_path: str, max_bytes: int = 200_000) -> str:
    """Read a UTF-8 text file under the sandbox. Large files are truncated to max_bytes."""
    p = _safe_join(relative_path)
    if not p.is_file():
        return f"Error: not a file: {relative_path!r}"
    data = p.read_bytes()
    truncated = len(data) > max_bytes
    chunk = data[:max_bytes]
    text = chunk.decode("utf-8", errors="replace")
    if truncated:
        return text + f"\n\n[truncated at {max_bytes} bytes]"
    return text


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
