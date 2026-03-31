"""End-to-end: Ollama chat with optional filesystem tool loop (async)."""

from __future__ import annotations

from typing import Any

import httpx

from omni.mcp_bridge import OLLAMA_TOOLS, exec_tool
from omni.ollama_chat import chat_with_tools_handled


async def run_turn(
    *,
    base_url: str,
    model: str,
    user_text: str,
    history: list[dict[str, Any]],
    use_fs_mcp: bool,
) -> tuple[str, list[dict[str, Any]]]:
    """Run one user turn; returns (assistant_text, updated_history)."""
    messages = [
        {"role": "system",
         "content": "You are a helpful assistant. When filesystem tools are available, "
                   "use them to read or list files under the configured sandbox root only."},
        *history,
        {"role": "user", "content": user_text},
    ]

    async with httpx.AsyncClient() as client:
        text, full = await chat_with_tools_handled(
            client, base_url, model, messages,
            tools=OLLAMA_TOOLS if use_fs_mcp else None,
            tool_executor=exec_tool if use_fs_mcp else None,
        )
    return text, full[1:]
