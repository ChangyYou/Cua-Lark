"""
Agent runtime (Plan then ReAct mode).
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime

from dotenv import load_dotenv

from app.skills import AgentSkill, build_skill_by_name, select_skill, skill_catalog_text

# High-risk keywords for human-in-the-loop interception
HIGH_RISK_KEYWORDS = re.compile(r"删除|清空|退出|解散")
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
from app.utils.memory import extract_and_store_memory, get_memory_guidance
from app.utils.skill_generator import analyze_and_generate_skill
from platforms import (
    CURRENT_PLATFORM,
    capture_lark_window,
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
        image_path = "captures/agent_capture.jpg"
    
    # Convert extension to .jpg if it's .png
    if image_path.lower().endswith(".png"):
        image_path = image_path[:-4] + ".jpg"
        
    output_dir = os.path.dirname(image_path) or "."
    os.makedirs(output_dir, exist_ok=True)
    
    # Compress image to speed up LLM API calls (avoids 300s timeout on slow network)
    image = image.convert("RGB")
    max_dim = 1920  # 提高到 1920，确保 1080P 屏幕截图完全不缩放分辨率
    if image.width > max_dim or image.height > max_dim:
        ratio = min(max_dim / image.width, max_dim / image.height)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        # Use LANCZOS for high-quality downsampling
        from PIL import Image
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        
    image.save(image_path, format="JPEG", quality=90)  # 提升画质到 90，减少 JPEG 伪影
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

        if action_type == "paste_content":
            from platforms import paste_text
            hwnd = grid_info.get("window_info", {}).get("hwnd")
            paste_text(str(action.get("text", "")), hwnd=hwnd)
            return True

        if action_type == "click_position":
            x_ratio = float(action.get("x_ratio", 0.5))
            y_ratio = float(action.get("y_ratio", 0.5))
            
            window_info = grid_info.get("window_info")
            if window_info:
                # 相对窗口的坐标
                abs_x = int(window_info["left"] + x_ratio * window_info["width"])
                abs_y = int(window_info["top"] + y_ratio * window_info["height"])
                hwnd = window_info.get("hwnd")
            else:
                # 相对整个屏幕（或截图）的坐标
                abs_x = int(x_ratio * grid_info.get("image_width", 1920))
                abs_y = int(y_ratio * grid_info.get("image_height", 1080))
                hwnd = None
                
            from platforms import click_at
            click_at(abs_x, abs_y, hwnd)
            return True

        if action_type == "press_key":
            key = str(action.get("key", "enter")).strip().lower()
            if key in ("command+k", "cmd+k", "ctrl+k", "control+k"):
                window_info = grid_info.get("window_info", {})
                open_search(window_info)
            elif "+" in key:
                from platforms.windows.hotkey import hotkey
                parts = [p.strip() for p in key.split("+") if p.strip()]
                hotkey(*parts)
            else:
                press(key)
            return True

        if action_type == "scroll":
            from platforms import scroll
            hwnd = grid_info.get("window_info", {}).get("hwnd")
            amount = int(action.get("amount", -500))
            scroll(amount, hwnd=hwnd) if hasattr(scroll, "__code__") and "hwnd" in scroll.__code__.co_varnames else scroll(amount)
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


def run_agent(user_command: str, grid_size: int = 6, debug: bool = False) -> tuple[bool, str]:
    """Run the agent in plan-then-react mode."""
    print("=" * 50)
    print("CUA-Lark Agent 启动（先规划后 ReAct）")
    print(f"当前平台: {CURRENT_PLATFORM}")
    print(f"用户命令: {user_command}")
    
    is_task_high_risk = bool(HIGH_RISK_KEYWORDS.search(user_command))
    if is_task_high_risk:
        print("⚠️ 注意：该任务被标记为高危任务，关键操作将需要您的二次确认。")
        
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

    memory_guidance = get_memory_guidance()

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
        memory_guidance=memory_guidance,
    )
    plan_text = call_llm_with_image(plan_prompt, image_path)
    if debug:
        print("LLM 原始计划输出:")
        print(plan_text)

    parsed_plan, error_msg = parse_plan(plan_text)
    if not parsed_plan:
        print(f"计划生成失败（失败原因: {error_msg}），回退到最小兜底计划。")
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
            memory_guidance=memory_guidance,
        )
        
        print("  正在调用大模型进行视觉决策，请稍候...")
        
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

        # 高危操作拦截 (Human-in-the-loop)
        action_reason = str(action.get("reason", ""))
        action_is_high_risk = is_task_high_risk or bool(HIGH_RISK_KEYWORDS.search(action_reason))
        
        if action_is_high_risk and action_type in ("click_position", "input_text", "press_key", "paste_content"):
            if action_type == "click_position":
                target_info = f"目标坐标：({action.get('x_ratio', 0):.3f}, {action.get('y_ratio', 0):.3f})"
            else:
                target_info = f"目标动作：{format_action_brief(action)}"
                
            print(f"\n⚠️ 警告：Agent 正在尝试执行 高危 操作。{target_info}")
            print(f"操作意图: {action_reason}")
            user_choice = input("是否允许继续？(y/n) [默认 n]: ").strip().lower()
            if user_choice != 'y':
                print("🚫 用户拒绝了该操作。")
                history.append({
                    "action": action, 
                    "success": False, 
                    "feedback": "用户拒绝了该操作"
                })
                if active_skill:
                    active_skill.on_action_result(action, False)
                print("  执行失败（被用户拦截），进入下一轮重新决策。")
                continue

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

    # 提取长期记忆
    if history:
        history_text = build_history_text(history)
        extract_and_store_memory(user_command, history_text, finished)
        
        # 如果是通用执行且执行成功，尝试固化为新技能
        if active_skill is None and finished:
            analyze_and_generate_skill(user_command, history_text)

    return finished, image_path

if __name__ == "__main__":
    run_agent("")

