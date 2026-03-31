"""Sandboxed filesystem tools exposed via MCP (stdio)."""

from __future__ import annotations

from mcp_filesystem.core import list_directory_impl, read_text_file_impl
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "aal-filesystem",
    instructions=(
        "Filesystem tools restricted to AAL_FS_ROOT (or the process working directory). "
        "Paths are relative to that root. Listing and reading text files only."
    ),
)


@mcp.tool()
def list_directory(relative_path: str = ".") -> str:
    """List files and subdirectories under the sandbox root."""
    return list_directory_impl(relative_path)


@mcp.tool()
def read_text_file(relative_path: str, max_bytes: int = 200_000) -> str:
    """Read a UTF-8 text file under the sandbox. Large files are truncated to max_bytes."""
    return read_text_file_impl(relative_path, max_bytes)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
