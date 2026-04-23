"""
LLM request helpers (plain, multimodal, function-calling).
"""

from __future__ import annotations

import json
import os
from typing import Any

import dashscope
from dashscope import MultiModalConversation

from app.config import config


def _setup_dashscope() -> None:
    """Configure DashScope SDK with API key and base URL."""
    dashscope.api_key = config.dashscope_api_key
    if config.dashscope_base_url:
        dashscope.base_url = config.dashscope_base_url


def _get_attr_or_key(obj: Any, name: str, default: Any = None) -> Any:
    """Read value from both dict-style and object-style SDK payloads."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _extract_text_content(response: Any) -> str:
    """Extract assistant plain text from DashScope response."""
    content = response.output.choices[0].message.content
    if isinstance(content, list):
        first_item = content[0]
        if isinstance(first_item, dict):
            return str(first_item.get("text", ""))
        return str(first_item)
    return str(content)


def call_llm_with_image(
    prompt: str,
    image_path: str,
    model: str | None = None,
    temperature: float | None = None,
) -> str:
    """Call multimodal model with one screenshot and one text prompt."""
    _setup_dashscope()
    model = model or config.model_image
    temperature = temperature if temperature is not None else config.model_temperature
    absolute_image_path = os.path.abspath(image_path)
    messages = [
        {
            "role": "user",
            "content": [
                {"image": f"file://{absolute_image_path}"},
                {"text": prompt},
            ],
        }
    ]

    try:
        response = MultiModalConversation.call(
            model=model,
            messages=messages,
            temperature=temperature,
        )
    except Exception as exc:
        print(f"LLM 调用异常: {exc}")
        return "[]"

    if response.status_code != 200:
        print(f"LLM 调用失败: {response.message}")
        return "[]"

    return _extract_text_content(response)


def call_llm_with_image_and_tools(
    prompt: str,
    image_path: str,
    tools: list[dict[str, Any]],
    model: str | None = None,
    temperature: float | None = None,
) -> dict[str, Any] | None:
    """Call multimodal model with function tools and return first tool call."""
    _setup_dashscope()
    model = model or config.model_tools
    temperature = temperature if temperature is not None else config.model_temperature
    absolute_image_path = os.path.abspath(image_path)
    messages = [
        {
            "role": "user",
            "content": [
                {"image": f"file://{absolute_image_path}"},
                {"text": prompt},
            ],
        }
    ]

    try:
        response = MultiModalConversation.call(
            model=model,
            messages=messages,
            temperature=temperature,
            tools=tools,
            tool_choice="auto",
        )
    except Exception as exc:
        print(f"LLM 工具调用异常: {exc}")
        return None

    if response.status_code != 200:
        print(f"LLM 工具调用失败: {response.message}")
        return None

    message = _get_attr_or_key(
        _get_attr_or_key(_get_attr_or_key(response, "output"), "choices", [{}])[0],
        "message",
    )
    tool_calls = _get_attr_or_key(message, "tool_calls", [])
    if not tool_calls:
        return None

    first_tool_call = tool_calls[0]
    function_payload = _get_attr_or_key(first_tool_call, "function", {})
    name = _get_attr_or_key(function_payload, "name", "")
    arguments_raw = _get_attr_or_key(function_payload, "arguments", "{}")

    if isinstance(arguments_raw, dict):
        arguments = arguments_raw
    else:
        try:
            arguments = json.loads(arguments_raw or "{}")
        except json.JSONDecodeError:
            arguments = {}

    if not name:
        return None
    return {"name": str(name), "arguments": arguments}


def call_llm_with_text_and_tools(
    prompt: str,
    tools: list[dict[str, Any]],
    model: str | None = None,
    temperature: float | None = None,
) -> dict[str, Any] | None:
    """Call model with text-only prompt and function tools."""
    _setup_dashscope()
    model = model or config.model_tools
    temperature = temperature if temperature is not None else config.model_temperature
    messages = [
        {
            "role": "user",
            "content": [{"text": prompt}],
        }
    ]

    try:
        response = MultiModalConversation.call(
            model=model,
            messages=messages,
            temperature=temperature,
            tools=tools,
            tool_choice="auto",
        )
    except Exception as exc:
        print(f"Skill 路由工具调用异常: {exc}")
        return None

    if response.status_code != 200:
        print(f"Skill 路由工具调用失败: {response.message}")
        return None

    message = _get_attr_or_key(
        _get_attr_or_key(_get_attr_or_key(response, "output"), "choices", [{}])[0],
        "message",
    )
    tool_calls = _get_attr_or_key(message, "tool_calls", [])
    if not tool_calls:
        return None

    first_tool_call = tool_calls[0]
    function_payload = _get_attr_or_key(first_tool_call, "function", {})
    name = _get_attr_or_key(function_payload, "name", "")
    arguments_raw = _get_attr_or_key(function_payload, "arguments", "{}")

    if isinstance(arguments_raw, dict):
        arguments = arguments_raw
    else:
        try:
            arguments = json.loads(arguments_raw or "{}")
        except json.JSONDecodeError:
            arguments = {}

    if not name:
        return None
    return {"name": str(name), "arguments": arguments}

