"""
Skill registry for CUA-Lark.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any, Protocol

SKILLS_ROOT = Path(__file__).resolve().parents[3] / "skills"

_loaded_skills = []

def _load_all_skills():
    """Dynamically load all skills from the skills directory."""
    global _loaded_skills
    if _loaded_skills:
        return

    if not SKILLS_ROOT.exists():
        return

    for skill_dir in SKILLS_ROOT.iterdir():
        if not skill_dir.is_dir() or skill_dir.name.startswith("__"):
            continue

        skill_name = skill_dir.name
        module_name = skill_name.replace("-", "_")
        script_path = skill_dir / "scripts" / f"{module_name}.py"

        if not script_path.exists():
            continue

        spec = importlib.util.spec_from_file_location(
            f"skill_{module_name}_runtime",
            str(script_path),
        )
        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"加载技能 {skill_name} 失败: {e}")
            continue

        skill_class = None
        describe_func = None

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if attr_name.endswith("Skill") and hasattr(attr, "try_create"):
                skill_class = attr
            elif attr_name.startswith("describe_") and callable(attr):
                describe_func = attr

        if skill_class and describe_func:
            _loaded_skills.append((skill_class, describe_func))


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
    _load_all_skills()
    normalized_name = (skill_name or "").strip().lower()
    
    for cls, describe in _loaded_skills:
        info = describe()
        if info["name"].strip().lower() == normalized_name:
            return cls.try_create(user_command)
    return None


def select_skill(user_command: str) -> AgentSkill | None:
    """
    Local fallback selector.
    Primary path should use function-calling router first.
    """
    _load_all_skills()
    for cls, _ in _loaded_skills:
        instance = cls.try_create(user_command)
        if instance:
            return instance
    return None


def skill_catalog_text() -> str:
    """Render skill catalog as plain text for prompts."""
    _load_all_skills()
    lines = ["[Skill Catalog]"]
    for _, describe in _loaded_skills:
        info = describe()
        lines.append(f"- name: {info['name']}")
        lines.append(f"  description: {info['description']}")
        lines.append(f"  trigger_condition: {info['trigger_condition']}")
    return "\n".join(lines)


__all__ = [
    "AgentSkill",
    "build_skill_by_name",
    "select_skill",
    "skill_catalog_text",
]
