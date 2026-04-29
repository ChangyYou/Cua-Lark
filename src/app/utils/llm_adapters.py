"""
LLM Adapter interface and implementations for CUA-Lark.
"""

from __future__ import annotations

import json
import base64
import os
from abc import ABC, abstractmethod
from typing import Any

from app.config import config

def _encode_image_to_base64(image_path: str) -> str:
    """Encode an image file to a base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


class BaseLLMClient(ABC):
    """Abstract base class for all LLM provider adapters."""

    @abstractmethod
    def call_with_image(
        self, prompt: str, image_path: str, model: str | None = None, temperature: float | None = None
    ) -> str:
        """Call multimodal model with one screenshot and one text prompt."""
        pass

    @abstractmethod
    def call_with_image_and_tools(
        self, prompt: str, image_path: str, tools: list[dict[str, Any]], model: str | None = None, temperature: float | None = None, system_prompt: str | None = None
    ) -> dict[str, Any] | None:
        """Call multimodal model with function tools and return first tool call."""
        pass

    @abstractmethod
    def call_with_text_and_tools(
        self, prompt: str, tools: list[dict[str, Any]], model: str | None = None, temperature: float | None = None
    ) -> dict[str, Any] | None:
        """Call model with text-only prompt and function tools."""
        pass


class DashScopeClient(BaseLLMClient):
    """Adapter for Alibaba DashScope SDK."""

    def _setup_dashscope(self) -> None:
        import dashscope
        dashscope.api_key = config.dashscope_api_key
        if config.dashscope_base_url:
            dashscope.base_url = config.dashscope_base_url

    def _get_attr_or_key(self, obj: Any, name: str, default: Any = None) -> Any:
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    def _extract_text_content(self, response: Any) -> str:
        content = response.output.choices[0].message.content
        if isinstance(content, list):
            first_item = content[0]
            if isinstance(first_item, dict):
                return str(first_item.get("text", ""))
            return str(first_item)
        return str(content)

    def call_with_image(
        self, prompt: str, image_path: str, model: str | None = None, temperature: float | None = None
    ) -> str:
        from dashscope import MultiModalConversation
        self._setup_dashscope()
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

        return self._extract_text_content(response)

    def call_with_image_and_tools(
        self, prompt: str, image_path: str, tools: list[dict[str, Any]], model: str | None = None, temperature: float | None = None, system_prompt: str | None = None
    ) -> dict[str, Any] | None:
        from dashscope import MultiModalConversation
        self._setup_dashscope()
        model = model or config.model_tools
        temperature = temperature if temperature is not None else config.model_temperature
        absolute_image_path = os.path.abspath(image_path)
        
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": [{"text": system_prompt}],
            })
            
        messages.append({
            "role": "user",
            "content": [
                {"image": f"file://{absolute_image_path}"},
                {"text": prompt},
            ],
        })

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

        message = self._get_attr_or_key(
            self._get_attr_or_key(self._get_attr_or_key(response, "output"), "choices", [{}])[0],
            "message",
        )
        tool_calls = self._get_attr_or_key(message, "tool_calls", [])
        if not tool_calls:
            return None

        first_tool_call = tool_calls[0]
        function_payload = self._get_attr_or_key(first_tool_call, "function", {})
        name = self._get_attr_or_key(function_payload, "name", "")
        arguments_raw = self._get_attr_or_key(function_payload, "arguments", "{}")

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

    def call_with_text_and_tools(
        self, prompt: str, tools: list[dict[str, Any]], model: str | None = None, temperature: float | None = None
    ) -> dict[str, Any] | None:
        from dashscope import MultiModalConversation
        self._setup_dashscope()
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

        message = self._get_attr_or_key(
            self._get_attr_or_key(self._get_attr_or_key(response, "output"), "choices", [{}])[0],
            "message",
        )
        tool_calls = self._get_attr_or_key(message, "tool_calls", [])
        if not tool_calls:
            return None

        first_tool_call = tool_calls[0]
        function_payload = self._get_attr_or_key(first_tool_call, "function", {})
        name = self._get_attr_or_key(function_payload, "name", "")
        arguments_raw = self._get_attr_or_key(function_payload, "arguments", "{}")

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


class OpenAIClient(BaseLLMClient):
    """Adapter for OpenAI SDK (e.g. GPT-4o, vLLM)."""

    def _get_client(self) -> Any:
        import openai
        api_key = config.openai_api_key
        base_url = config.openai_base_url if config.openai_base_url else None
        return openai.OpenAI(api_key=api_key, base_url=base_url)

    def call_with_image(
        self, prompt: str, image_path: str, model: str | None = None, temperature: float | None = None
    ) -> str:
        client = self._get_client()
        model = model or config.model_image
        temperature = temperature if temperature is not None else config.model_temperature
        
        base64_image = _encode_image_to_base64(image_path)
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ],
            }
        ]

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            return str(response.choices[0].message.content)
        except Exception as exc:
            print(f"OpenAI LLM 调用异常: {exc}")
            return "[]"

    def call_with_image_and_tools(
        self, prompt: str, image_path: str, tools: list[dict[str, Any]], model: str | None = None, temperature: float | None = None, system_prompt: str | None = None
    ) -> dict[str, Any] | None:
        client = self._get_client()
        model = model or config.model_tools
        temperature = temperature if temperature is not None else config.model_temperature
        
        base64_image = _encode_image_to_base64(image_path)
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": system_prompt
                    }
                ],
            })
            
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ],
        })
        
        # OpenAI expects tools to be wrapped in specific format
        formatted_tools = []
        for tool in tools:
            formatted_tools.append({
                "type": "function",
                "function": tool
            })

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                tools=formatted_tools,
                tool_choice="auto",
            )
        except Exception as exc:
            print(f"OpenAI LLM 工具调用异常: {exc}")
            return None

        message = response.choices[0].message
        if not message.tool_calls:
            return None

        first_tool_call = message.tool_calls[0]
        function_payload = first_tool_call.function
        name = function_payload.name
        arguments_raw = function_payload.arguments

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

    def call_with_text_and_tools(
        self, prompt: str, tools: list[dict[str, Any]], model: str | None = None, temperature: float | None = None
    ) -> dict[str, Any] | None:
        client = self._get_client()
        model = model or config.model_tools
        temperature = temperature if temperature is not None else config.model_temperature
        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]
        
        formatted_tools = []
        for tool in tools:
            formatted_tools.append({
                "type": "function",
                "function": tool
            })

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                tools=formatted_tools,
                tool_choice="auto",
            )
        except Exception as exc:
            print(f"OpenAI Skill 路由工具调用异常: {exc}")
            return None

        message = response.choices[0].message
        if not message.tool_calls:
            return None

        first_tool_call = message.tool_calls[0]
        function_payload = first_tool_call.function
        name = function_payload.name
        arguments_raw = function_payload.arguments

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


def get_llm_client() -> BaseLLMClient:
    """Factory function to return the correct LLM client based on config."""
    provider = config.llm_provider
    if provider == "openai":
        return OpenAIClient()
    # Default to dashscope
    return DashScopeClient()
