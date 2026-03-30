"""Connect to an MCP server over stdio and expose tools to the chat layer."""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

import mcp.types as types
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from omni.paths import fs_mcp_executable


def mcp_tool_to_ollama(tool: types.Tool) -> dict[str, Any]:
    schema = tool.inputSchema
    if isinstance(schema, dict) and schema:
        parameters = schema
    else:
        parameters = {"type": "object", "properties": {}}
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": parameters,
        },
    }


def _src_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _stdio_params_fs() -> StdioServerParameters:
    bundled = fs_mcp_executable()
    if bundled is not None:
        return StdioServerParameters(command=str(bundled), args=[])

    env = {**os.environ, "PYTHONPATH": str(_src_root())}
    return StdioServerParameters(command=sys.executable, args=["-m", "mcp_filesystem"], env=env)


def tool_result_to_text(result: types.CallToolResult) -> str:
    parts: list[str] = []
    for block in result.content:
        if getattr(block, "type", None) == "text" and hasattr(block, "text"):
            parts.append(str(block.text))
        else:
            parts.append(str(block))
    if result.isError:
        return "Error: " + ("\n".join(parts) if parts else "unknown")
    return "\n".join(parts) if parts else ""


@asynccontextmanager
async def fs_mcp_session() -> AsyncIterator[ClientSession]:
    params = _stdio_params_fs()
    # Windows subprocess needs a real OS file handle for stderr (StringIO breaks).
    try:
        devnull = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115
        errlog = devnull
    except OSError:
        devnull = None
        errlog = sys.stderr
    try:
        async with stdio_client(params, errlog=errlog) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
    finally:
        if devnull is not None:
            devnull.close()
