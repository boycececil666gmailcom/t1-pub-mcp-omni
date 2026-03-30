"""Ollama /api/chat with optional tool loop (OpenAI-style tools)."""

from __future__ import annotations

import json
from typing import Any

import httpx

OLLAMA_CHAT = "/api/chat"


def _normalize_tool_arguments(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            return {}
    return {}


async def chat_with_tools_handled(
    client: httpx.AsyncClient,
    base_url: str,
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None,
    tool_executor,
    *,
    max_tool_rounds: int = 8,
) -> tuple[str, list[dict[str, Any]]]:
    """tool_executor: async (name: str, arguments: dict) -> str"""

    url = base_url.rstrip("/") + OLLAMA_CHAT
    current = list(messages)
    visible_parts: list[str] = []

    for _ in range(max_tool_rounds):
        body: dict[str, Any] = {
            "model": model,
            "messages": current,
            "stream": False,
        }
        if tools:
            body["tools"] = tools

        r = await client.post(url, json=body, timeout=600.0)
        r.raise_for_status()
        data = r.json()
        msg = data.get("message") or {}
        role = msg.get("role", "assistant")
        content = msg.get("content") or ""
        tool_calls = msg.get("tool_calls")

        entry: dict[str, Any] = {"role": role, "content": content}
        if tool_calls:
            entry["tool_calls"] = tool_calls
        current.append(entry)

        if content and isinstance(content, str) and content.strip():
            visible_parts.append(content.strip())

        if not tool_calls:
            break

        for call in tool_calls:
            fn = call.get("function") or {}
            name = str(fn.get("name") or "")
            args = _normalize_tool_arguments(fn.get("arguments"))
            try:
                result_text = await tool_executor(name, args)
            except Exception as exc:  # noqa: BLE001
                result_text = f"Tool error: {exc}"
            tool_message: dict[str, Any] = {
                "role": "tool",
                "content": result_text,
            }
            if call.get("id") is not None:
                tool_message["tool_call_id"] = call["id"]
            if name:
                tool_message["name"] = name
            current.append(tool_message)

    return "\n\n".join(visible_parts) if visible_parts else "", current
