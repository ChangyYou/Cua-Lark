"""
LLM request helpers (plain, multimodal, function-calling).
This module acts as a facade over the underlying LLM Adapters.
"""

from __future__ import annotations

from typing import Any

from app.utils.llm_adapters import get_llm_client

def call_llm_with_image(
    prompt: str,
    image_path: str,
    model: str | None = None,
    temperature: float | None = None,
) -> str:
    """Call multimodal model with one screenshot and one text prompt."""
    client = get_llm_client()
    return client.call_with_image(prompt, image_path, model, temperature)

def call_llm_with_image_and_tools(
    prompt: str,
    image_path: str,
    tools: list[dict[str, Any]],
    model: str | None = None,
    temperature: float | None = None,
    system_prompt: str | None = None,
) -> dict[str, Any] | None:
    """Call multimodal model with function tools and return first tool call."""
    client = get_llm_client()
    return client.call_with_image_and_tools(prompt, image_path, tools, model, temperature, system_prompt)

def call_llm_with_text_and_tools(
    prompt: str,
    tools: list[dict[str, Any]],
    model: str | None = None,
    temperature: float | None = None,
) -> dict[str, Any] | None:
    """Call model with text-only prompt and function tools."""
    client = get_llm_client()
    return client.call_with_text_and_tools(prompt, tools, model, temperature)
