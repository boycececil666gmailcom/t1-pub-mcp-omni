"""Standalone stdio MCP server — exposes filesystem tools over stdio transport."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_filesystem.core import list_directory_impl, read_text_file_impl

mcp = FastMCP(
    "aal-filesystem",
    instructions=(
        "Filesystem tools restricted to AAL_FS_ROOT (or the process working directory). "
        "Paths are relative to that root. Listing and reading text files only."
    ),
)


@mcp.tool()
def list_directory(relative_path: str = ".") -> str:
    return list_directory_impl(relative_path)


@mcp.tool()
def read_text_file(relative_path: str, max_bytes: int = 200_000) -> str:
    return read_text_file_impl(relative_path, max_bytes)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
