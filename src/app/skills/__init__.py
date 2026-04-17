"""
Skill registry for CUA-Lark.
"""

from __future__ import annotations

from typing import Any, Protocol

from app.skills.send_message import SendMessageSkill, describe_send_message_skill


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
        return SendMessageSkill.try_create(user_command)
    return None


def select_skill(user_command: str) -> AgentSkill | None:
    """
    Local fallback selector.

    Primary path should use function-calling router first.
    """
    return SendMessageSkill.try_create(user_command)


def skill_catalog_text() -> str:
    """Render skill catalog as plain text for prompts."""
    info = describe_send_message_skill()
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

