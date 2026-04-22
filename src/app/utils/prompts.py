"""
Prompt loader and template builders.
"""

from __future__ import annotations

from pathlib import Path
import re

PROMPT_FILE = Path(__file__).resolve().parents[3] / "Prompt" / "agent_prompts.md"

FALLBACK_SKILL_ROUTER_PROMPT = """你是一个技能路由器，需要根据用户目标判断是否激活某个 skill。

用户目标：{user_command}

可用技能：
{skill_catalog}

规则：
- 只能通过 function calling 决策，且只调用一次。
- 若用户目标明确满足某个 skill 的 trigger_condition，调用 activate_skill。
- 若不满足任何 skill，调用 skip_skill。
- activate_skill 的 name 必须与 skill catalog 中的 name 完全一致。
- 不要输出解释文本。
"""

FALLBACK_PLAN_PROMPT = """你是一个桌面操作智能体，正在操控飞书桌面客户端。

用户目标：{user_command}

{skill_catalog}

请基于截图输出 JSON 计划（数组）。
动作仅可使用：open_search / click_position / input_text / press_key / wait / done
- 最后一步必须 done
- 不确定时优先 wait
- 点击操作使用 click_position
{skill_guidance}
"""

FALLBACK_REACT_PROMPT = """你是一个桌面操作智能体（ReAct 阶段）。

用户目标：{user_command}
轮次：{step_index}/{max_steps}
初始计划：
{initial_plan_text}
历史：
{history_text}

{skill_catalog}

必须用 function calling，每轮只调一个函数：click_position / press_key / paste_content
- 不确定时优先 wait
- 目标完成时输出 done
- 点击操作使用 click_position 给出坐标比例
{skill_guidance}
"""


def load_prompt_section(section_name: str) -> str | None:
    """
    Load section fenced by:
      ## SECTION_NAME
      ```prompt
      ...
      ```
    """
    try:
        content = PROMPT_FILE.read_text(encoding="utf-8")
    except OSError:
        return None

    pattern = rf"##\s+{re.escape(section_name)}\s*\n```(?:prompt|text)?\n(.*?)\n```"
    match = re.search(pattern, content, flags=re.DOTALL)
    if not match:
        return None
    return match.group(1).strip()


def get_skill_router_prompt_template() -> str:
    return load_prompt_section("SKILL_ROUTER_PROMPT") or FALLBACK_SKILL_ROUTER_PROMPT


def get_plan_prompt_template() -> str:
    return load_prompt_section("PLAN_PROMPT_TEMPLATE") or FALLBACK_PLAN_PROMPT


def get_react_prompt_template() -> str:
    return load_prompt_section("REACT_PROMPT_TEMPLATE") or FALLBACK_REACT_PROMPT


def build_skill_router_prompt(user_command: str, skill_catalog: str) -> str:
    template = get_skill_router_prompt_template()
    return template.format(
        user_command=user_command,
        skill_catalog=skill_catalog,
    )


def build_plan_prompt(
    user_command: str,
    grid_size: int,
    cell_width: float,
    cell_height: float,
    max_plan_steps: int,
    skill_catalog: str,
    skill_guidance: str,
) -> str:
    template = get_plan_prompt_template()
    return template.format(
        user_command=user_command,
        grid_size=grid_size,
        cell_width=cell_width,
        cell_height=cell_height,
        max_plan_steps=max_plan_steps,
        skill_catalog=skill_catalog,
        skill_guidance=skill_guidance,
    )


def build_react_prompt(
    user_command: str,
    step_index: int,
    max_steps: int,
    initial_plan_text: str,
    history_text: str,
    grid_size: int,
    cell_width: float,
    cell_height: float,
    skill_catalog: str,
    skill_guidance: str,
) -> str:
    template = get_react_prompt_template()
    return template.format(
        user_command=user_command,
        step_index=step_index,
        max_steps=max_steps,
        initial_plan_text=initial_plan_text,
        history_text=history_text,
        grid_size=grid_size,
        cell_width=cell_width,
        cell_height=cell_height,
        skill_catalog=skill_catalog,
        skill_guidance=skill_guidance,
    )

