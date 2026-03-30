"""End-to-end: Ollama chat with optional filesystem tool loop (async)."""

from __future__ import annotations

from typing import Any

import httpx

from omni.mcp_bridge import OLLAMA_TOOLS, exec_tool, tool_result_to_text
from omni.ollama_chat import chat_with_tools_handled


async def run_turn(
    *,
    base_url: str,
    model: str,
    user_text: str,
    history: list[dict[str, Any]],
    use_fs_mcp: bool,
) -> tuple[str, list[dict[str, Any]]]:
    """
    history: Ollama-format messages without the system prompt (user/assistant/tool only).
    Returns (assistant_visible_text, new_history including this turn).
    """
    system: dict[str, Any] = {
        "role": "system",
        "content": (
            "You are a helpful assistant. When filesystem tools are available, "
            "use them to read or list files under the configured sandbox root only."
        ),
    }
    messages: list[dict[str, Any]] = [
        system,
        *history,
        {"role": "user", "content": user_text},
    ]

    async with httpx.AsyncClient() as client:
        if not use_fs_mcp:
            text, full = await chat_with_tools_handled(
                client, base_url, model, messages, None, _noop_executor
            )
            return text, full[1:]

        text, full = await chat_with_tools_handled(
            client, base_url, model, messages, OLLAMA_TOOLS, exec_tool
        )
        return text, full[1:]


async def _noop_executor(_name: str, _args: dict[str, Any]) -> str:
    return ""
