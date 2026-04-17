"""
Action parsing/normalization helpers.
"""

from __future__ import annotations

import json
from typing import Any


def parse_plan(content: str) -> list[dict[str, Any]]:
    """Parse a JSON action plan from model output."""
    text = (content or "").strip()
    if not text:
        return []

    if "```" in text:
        first = text.find("```")
        last = text.rfind("```")
        if first != -1 and last != -1 and last > first:
            text = text[first + 3 : last].strip()
            if text.startswith("json"):
                text = text[4:].strip()

    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []

    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        print(f"计划解析失败: {exc}")
        return []

    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def normalize_action(action: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize aliases and fill defaults."""
    if not action:
        return {"action": "wait", "seconds": 1, "reason": "兜底：空动作"}

    action_type = str(action.get("action", "")).strip().lower()
    alias_map = {
        "click": "click_grid",
        "type": "input_text",
        "paste": "input_text",
        "press": "press_key",
    }
    action_type = alias_map.get(action_type, action_type)

    normalized = dict(action)
    normalized["action"] = action_type

    if action_type == "click_grid":
        try:
            grid = int(normalized.get("grid"))
        except (TypeError, ValueError):
            return {
                "action": "wait",
                "seconds": 0.8,
                "reason": "兜底：click_grid 缺少有效 grid，等待下一轮重新定位",
            }
        if grid < 1:
            return {
                "action": "wait",
                "seconds": 0.8,
                "reason": "兜底：click_grid 的 grid 非法，等待下一轮重新定位",
            }
        normalized["grid"] = grid
        normalized.setdefault("offset_ratio", 0.5)
    elif action_type == "wait":
        try:
            seconds = float(normalized.get("seconds", 1))
        except (TypeError, ValueError):
            seconds = 1.0
        normalized["seconds"] = max(0.3, min(seconds, 20.0))
    elif action_type == "press_key":
        normalized.setdefault("key", "enter")
    elif action_type == "input_text":
        normalized.setdefault("text", "")

    normalized.setdefault("reason", "")
    return normalized


def action_from_tool_call(tool_call: dict[str, Any] | None) -> dict[str, Any]:
    """Convert one function-calling tool invocation to internal action schema."""
    if not tool_call:
        return {"action": "wait", "seconds": 0.8, "reason": "兜底：未收到工具调用"}

    name = str(tool_call.get("name", "")).strip()
    arguments = tool_call.get("arguments", {}) or {}
    reason = str(arguments.get("reason", "")).strip()

    if name == "click_region":
        return normalize_action(
            {
                "action": "click_grid",
                "grid": arguments.get("grid"),
                "offset_ratio": arguments.get("offset_ratio", 0.5),
                "reason": reason or "函数调用：点击区域",
            }
        )

    if name == "press_key":
        return normalize_action(
            {
                "action": "press_key",
                "key": str(arguments.get("key", "")).strip(),
                "reason": reason or "函数调用：按下按键",
            }
        )

    if name == "paste_content":
        return normalize_action(
            {
                "action": "input_text",
                "text": str(arguments.get("text", "")),
                "reason": reason or "函数调用：粘贴内容",
            }
        )

    return {"action": "wait", "seconds": 0.8, "reason": f"兜底：未知函数 {name}"}


def normalize_plan(plan: list[dict[str, Any]], max_plan_steps: int) -> list[dict[str, Any]]:
    """Normalize plan actions and cap total step count."""
    normalized: list[dict[str, Any]] = []
    for raw_action in plan:
        normalized.append(normalize_action(raw_action))
        if len(normalized) >= max_plan_steps:
            break

    if not normalized or normalized[-1].get("action") != "done":
        normalized.append({"action": "done", "reason": "计划末尾补充完成标记"})

    return normalized


def format_action_brief(action: dict[str, Any]) -> str:
    """Format action for concise plan/history text."""
    action_type = str(action.get("action", "unknown"))
    if action_type == "wait":
        return f"wait({action.get('seconds', 1)}s)"
    if action_type == "click_grid":
        return f"click_grid({action.get('grid', '?')})"
    if action_type == "input_text":
        text = str(action.get("text", ""))
        if len(text) > 14:
            text = text[:14] + "..."
        return f'input_text("{text}")'
    if action_type == "press_key":
        return f"press_key({action.get('key', 'enter')})"
    return action_type


def build_initial_plan_text(plan: list[dict[str, Any]]) -> str:
    """Render initial plan as numbered lines for ReAct prompt."""
    lines = []
    for idx, action in enumerate(plan, start=1):
        lines.append(f"{idx}. {format_action_brief(action)} - {str(action.get('reason', ''))}")
    return "\n".join(lines) if lines else "无"


def build_history_text(history: list[dict[str, Any]], max_items: int = 10) -> str:
    """Render recent execution history for ReAct prompt."""
    if not history:
        return "无"
    start = max(0, len(history) - max_items)
    lines = []
    for idx, item in enumerate(history[start:], start=start + 1):
        status = "成功" if item.get("success") else "失败"
        lines.append(f"{idx}. {format_action_brief(item.get('action', {}))} [{status}]")
    return "\n".join(lines)
