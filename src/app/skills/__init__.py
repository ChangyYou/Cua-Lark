"""
Skill registry for CUA-Lark.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any, Protocol

SEND_MESSAGE_RUNTIME = (
    Path(__file__).resolve().parents[3]
    / "skills"
    / "send-message"
    / "scripts"
    / "send_message.py"
)

_runtime_module = None


def _load_runtime_module():
    """Load send-message runtime module from skill scripts directory."""
    global _runtime_module
    if _runtime_module is not None:
        return _runtime_module

    if not SEND_MESSAGE_RUNTIME.exists():
        raise FileNotFoundError(f"skill runtime 不存在: {SEND_MESSAGE_RUNTIME}")

    spec = importlib.util.spec_from_file_location(
        "skill_send_message_runtime",
        str(SEND_MESSAGE_RUNTIME),
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载 skill runtime: {SEND_MESSAGE_RUNTIME}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _runtime_module = module
    return module


def _send_message_api():
    """Return runtime API from loaded module."""
    module = _load_runtime_module()
    return module.SendMessageSkill, module.describe_send_message_skill


class AgentSkill(Protocol):
    """Minimal protocol for pluggable skills."""

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def trigger_condition(self) -> str: ...

    def plan_guidance(self) -> str: ...

    def react_guidance(self) -> str: ...

    def enforce_action(self, action: dict[str, Any]) -> dict[str, Any]: ...

    def on_action_result(self, action: dict[str, Any], success: bool) -> None: ...

    def allow_done(self) -> bool: ...


def build_skill_by_name(skill_name: str, user_command: str) -> AgentSkill | None:
    """Instantiate one skill by name."""
    normalized_name = (skill_name or "").strip().lower()
    if normalized_name in ("send-message", "send_message"):
        send_cls, _ = _send_message_api()
        return send_cls.try_create(user_command)
    return None


def select_skill(user_command: str) -> AgentSkill | None:
    """
    Local fallback selector.

    Primary path should use function-calling router first.
    """
    send_cls, _ = _send_message_api()
    return send_cls.try_create(user_command)


def skill_catalog_text() -> str:
    """Render skill catalog as plain text for prompts."""
    _, describe = _send_message_api()
    info = describe()
    return (
        "[Skill Catalog]\n"
        f"- name: {info['name']}\n"
        f"  description: {info['description']}\n"
        f"  trigger_condition: {info['trigger_condition']}"
    )


__all__ = [
    "AgentSkill",
    "build_skill_by_name",
    "select_skill",
    "skill_catalog_text",
]
