"""
Agent runtime (Plan then ReAct mode).
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime

from dotenv import load_dotenv

from app.skills import AgentSkill, build_skill_by_name, select_skill, skill_catalog_text
from app.utils.actions import (
    action_from_tool_call,
    build_history_text,
    build_initial_plan_text,
    format_action_brief,
    normalize_action,
    normalize_plan,
    parse_plan,
)
from app.utils.llm import (
    call_llm_with_image,
    call_llm_with_image_and_tools,
    call_llm_with_text_and_tools,
)
from app.utils.prompts import build_plan_prompt, build_react_prompt, build_skill_router_prompt
from app.utils.tools import REACT_FUNCTION_TOOLS, SKILL_ROUTER_FUNCTION_TOOLS
from platforms import (
    CURRENT_PLATFORM,
    capture_lark_window,
    click_grid_bottom,
    input_message,
    open_search,
    press,
)

# Load environment variables before configuring SDK clients.
load_dotenv()

MAX_PLAN_STEPS = 20
MAX_REACT_STEPS = 25


def capture_and_prepare(grid_size: int = 6, image_path: str | None = None) -> tuple[str, dict]:
    """Capture current Lark window and persist screenshot."""
    image, grid_info = capture_lark_window(grid_size=grid_size)
    if image_path is None:
        image_path = "captures/agent_capture.png"
    output_dir = os.path.dirname(image_path) or "."
    os.makedirs(output_dir, exist_ok=True)
    image.save(image_path)
    return image_path, grid_info


def resolve_active_skill(user_command: str, skill_catalog: str, debug: bool = False) -> AgentSkill | None:
    """
    Skill routing via function calling first, with local fallback.
    """
    router_prompt = build_skill_router_prompt(user_command=user_command, skill_catalog=skill_catalog)
    router_call = call_llm_with_text_and_tools(
        prompt=router_prompt,
        tools=SKILL_ROUTER_FUNCTION_TOOLS,
    )

    if debug:
        print("\nSkill Router 工具调用:")
        print(json.dumps(router_call, ensure_ascii=False) if router_call else "None")

    if router_call:
        tool_name = str(router_call.get("name", "")).strip()
        arguments = router_call.get("arguments", {}) or {}

        if tool_name == "activate_skill":
            routed_skill_name = str(arguments.get("name", "")).strip()
            routed_skill = build_skill_by_name(routed_skill_name, user_command)
            if routed_skill:
                return routed_skill
            print(f"Skill 路由命中但实例化失败: {routed_skill_name}，回退本地匹配。")

        if tool_name == "skip_skill":
            return None

    fallback_skill = select_skill(user_command)
    if fallback_skill:
        print("Skill 路由回退：本地规则命中。")
    return fallback_skill


def execute_action(action: dict, grid_info: dict) -> bool:
    """Execute one action from ReAct decision."""
    action_type = action.get("action", "")
    reason = action.get("reason", "")
    print(f"  执行: {action_type} - {reason}")

    try:
        if action_type == "open_search":
            window_info = grid_info.get("window_info", {})
            open_search(window_info)
            return True

        if action_type == "input_text":
            input_message(str(action.get("text", "")))
            return True

        if action_type == "click_grid":
            if "grid" not in action:
                print("  缺少 grid 参数，跳过点击。")
                return False
            click_grid_bottom(
                int(action["grid"]),
                grid_info,
                float(action.get("offset_ratio", 0.5)),
            )
            return True

        if action_type == "press_key":
            key = str(action.get("key", "enter")).strip().lower()
            if key in ("command+k", "cmd+k", "ctrl+k", "control+k"):
                window_info = grid_info.get("window_info", {})
                open_search(window_info)
            else:
                press(key)
            return True

        if action_type == "wait":
            seconds = float(action.get("seconds", 1))
            print(f"  等待 {seconds:.1f} 秒...")
            time.sleep(seconds)
            return True

        if action_type == "done":
            return True

        print(f"  未知动作: {action_type}")
        return False
    except Exception as exc:
        print(f"  执行异常: {exc}")
        return False


def run_agent(user_command: str, grid_size: int = 6, debug: bool = False) -> None:
    """Run the agent in plan-then-react mode."""
    print("=" * 50)
    print("CUA-Lark Agent 启动（先规划后 ReAct）")
    print(f"当前平台: {CURRENT_PLATFORM}")
    print(f"用户命令: {user_command}")
    if debug:
        print("调试模式: 开启")
    print("=" * 50)

    skill_catalog = skill_catalog_text()
    active_skill = resolve_active_skill(user_command, skill_catalog, debug=debug)
    if active_skill:
        print(f"已激活技能: {active_skill.name}")
        print(f"技能描述: {active_skill.description}")
        print(f"触发条件: {active_skill.trigger_condition}")
    else:
        print("未激活技能：走通用执行。")

    run_tag = datetime.now().strftime("%Y%m%d-%H%M%S")
    capture_dir = os.path.join("captures", f"run-{run_tag}")
    os.makedirs(capture_dir, exist_ok=True)
    print(f"截图保存目录: {capture_dir}")

    print("\n【步骤 1】观察当前界面并生成任务计划...")
    plan_observe_path = os.path.join(capture_dir, "plan-00-observe.png")
    image_path, grid_info = capture_and_prepare(grid_size=grid_size, image_path=plan_observe_path)

    plan_prompt = build_plan_prompt(
        user_command=user_command,
        grid_size=int(grid_info.get("grid_size", 6)),
        cell_width=float(grid_info.get("cell_width", 0.0)),
        cell_height=float(grid_info.get("cell_height", 0.0)),
        max_plan_steps=MAX_PLAN_STEPS,
        skill_catalog=skill_catalog,
        skill_guidance=active_skill.plan_guidance() if active_skill else "",
    )
    plan_text = call_llm_with_image(plan_prompt, image_path)
    if debug:
        print("LLM 原始计划输出:")
        print(plan_text)

    parsed_plan = parse_plan(plan_text)
    if not parsed_plan:
        print("计划生成失败，回退到最小兜底计划。")
        parsed_plan = [{"action": "wait", "seconds": 1, "reason": "兜底等待"}, {"action": "done"}]
    plan = normalize_plan(parsed_plan, max_plan_steps=MAX_PLAN_STEPS)

    print(f"\n初始计划（共 {len(plan)} 步）:")
    for index, step in enumerate(plan, start=1):
        action_type = step.get("action")
        reason = step.get("reason", "")
        if action_type == "wait":
            print(f"  {index}. wait({step.get('seconds', 1)}s): {reason}")
        else:
            print(f"  {index}. {action_type}: {reason}")

    print("\n【步骤 2】ReAct 执行（每步基于最新截图决策）...")
    finished = False
    history: list[dict] = []
    for step_index in range(1, MAX_REACT_STEPS + 1):
        before_path = os.path.join(capture_dir, f"step-{step_index:02d}-observe.png")
        image_path, latest_grid_info = capture_and_prepare(grid_size=grid_size, image_path=before_path)

        react_prompt = build_react_prompt(
            user_command=user_command,
            step_index=step_index,
            max_steps=MAX_REACT_STEPS,
            initial_plan_text=build_initial_plan_text(plan),
            history_text=build_history_text(history),
            grid_size=int(latest_grid_info.get("grid_size", 6)),
            cell_width=float(latest_grid_info.get("cell_width", 0.0)),
            cell_height=float(latest_grid_info.get("cell_height", 0.0)),
            skill_catalog=skill_catalog,
            skill_guidance=active_skill.react_guidance() if active_skill else "",
        )
        tool_call = call_llm_with_image_and_tools(
            prompt=react_prompt,
            image_path=image_path,
            tools=REACT_FUNCTION_TOOLS,
        )

        if tool_call and debug:
            print("\nLLM ReAct 工具调用:")
            print(json.dumps(tool_call, ensure_ascii=False))

        action = action_from_tool_call(tool_call)
        if active_skill:
            action = normalize_action(active_skill.enforce_action(action))
        action_type = str(action.get("action", ""))
        print(f"\n  [{step_index}/{MAX_REACT_STEPS}] {format_action_brief(action)}")

        if action_type == "done":
            if active_skill and not active_skill.allow_done():
                print("  技能流程未完成，忽略 done 并继续。")
                continue
            print("  LLM 判定任务完成。")
            finished = True
            break

        success = execute_action(action, latest_grid_info)
        history.append({"action": action, "success": success})
        if active_skill:
            active_skill.on_action_result(action, success)
        if not success:
            print("  执行失败，进入下一轮重新决策。")

        time.sleep(1.0)

    print("\n" + "=" * 50)
    if finished:
        print("任务完成！")
    else:
        print(f"达到最大 ReAct 轮次 {MAX_REACT_STEPS}，执行结束。")
    print("=" * 50)


if __name__ == "__main__":
    run_agent("")

