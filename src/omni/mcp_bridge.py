"""In-process MCP bridge — no subprocess, no visible console window.

Architecture
────────────
The OmniFsMcp.exe subprocess is eliminated entirely.
The filesystem tools (list_directory, read_text_file) are called directly
from the same asyncio worker that runs the Ollama chat loop, after setting
OMNI_FS_ROOT in that thread's environment.  Tool schemas are kept in
Ollama's OpenAI-style format so chat_pipeline.py can use them without
any stdio transport.
"""

from __future__ import annotations

import os
from typing import Any

from mcp_filesystem.core import list_directory_impl, read_text_file_impl


# ─────────────────────────────────────────────────────────────────────────────
# Ollama-format tool schemas (no MCP transport needed)
# ─────────────────────────────────────────────────────────────────────────────

OLLAMA_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": (
                "List files and subdirectories under the configured sandbox root. "
                "Pass '.' or an empty string to list the root; "
                "pass a relative path like 'src' or 'src/utils' to list a subdirectory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "default": ".",
                        "description": "Relative path under the sandbox root.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_text_file",
            "description": (
                "Read the contents of a UTF-8 text file under the sandbox root. "
                "Large files are truncated at max_bytes (default 200 000). "
                "Only text files are supported."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": "Relative path of the file under the sandbox root.",
                    },
                    "max_bytes": {
                        "type": "integer",
                        "default": 200_000,
                        "description": "Maximum number of bytes to read.",
                    },
                },
                "required": ["relative_path"],
            },
        },
    },
]


def tool_result_to_text(result: str) -> str:
    """Normalise a tool result to a plain string for the model."""
    if not result:
        return ""
    return result


async def exec_tool(name: str, arguments: dict[str, Any]) -> str:
    """Execute a filesystem tool directly in the current asyncio context.

    OMNI_FS_ROOT must already be set in the caller's environment
    (chat_pipeline.py sets it in the worker thread before asyncio.run)."""
    match name:
        case "list_directory":
            return list_directory_impl(arguments.get("relative_path", "."))
        case "read_text_file":
            return read_text_file_impl(
                arguments.get("relative_path", ""),
                arguments.get("max_bytes", 200_000),
            )
        case _:
            return f"Error: unknown tool {name!r}"
