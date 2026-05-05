import sys
import os
import base64
import asyncio
import json

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from pathlib import Path
from typing import AsyncIterator


def encode_image_to_base64(image_path: str) -> str:
    """Encode image to base64 for frontend display."""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


class AgentBridge:
    """Bridge to communicate with the existing Agent."""

    async def execute_streaming(self, command: str) -> AsyncIterator[dict]:
        """
        Execute command and yield step events.
        Each event has: type ('step'|'done'|'error'), and data.
        """
        try:
            from app.agent import (
                capture_and_prepare,
                resolve_active_skill,
                skill_catalog_text,
                get_memory_guidance,
                MAX_REACT_STEPS,
                MAX_PLAN_STEPS,
            )
            from app.utils.actions import (
                build_initial_plan_text,
                build_history_text,
                parse_plan,
                normalize_plan,
                action_from_tool_call,
                format_action_brief,
                normalize_action,
            )
            from app.utils.prompts import build_plan_prompt, build_react_prompt
            from app.utils.llm import call_llm_with_image, call_llm_with_image_and_tools
            from app.utils.tools import REACT_FUNCTION_TOOLS

            print("\n" + "=" * 60)
            print(f"[Bridge] 收到命令: {command}")
            print("=" * 60)

            # Skill 路由阶段
            print("\n【Skill 路由】")
            skill_catalog = skill_catalog_text()
            active_skill = resolve_active_skill(command, skill_catalog, debug=True)

            skill_name = None
            if active_skill:
                skill_name = active_skill.name
                print(f"✓ 技能激活成功: {active_skill.name}")
                print(f"  描述: {active_skill.description}")
                print(f"  触发条件: {active_skill.trigger_condition}")
                print(f"  当前阶段: {active_skill.stage}")
            else:
                print("✗ 未激活任何技能，将使用通用执行模式")

            capture_dir = os.path.join("captures", f"run-{int(asyncio.get_event_loop().time() * 1000)}")
            os.makedirs(capture_dir, exist_ok=True)
            print(f"\n截图保存目录: {capture_dir}")

            memory_guidance = get_memory_guidance()
            if memory_guidance:
                print(f"长期记忆已加载 (长度: {len(memory_guidance)} 字符)")

            # Plan 阶段
            print("\n" + "-" * 60)
            print("【Plan 阶段】生成任务计划...")
            print("-" * 60)

            plan_observe_path = os.path.join(capture_dir, "plan-00-observe.png")
            image_path, grid_info = capture_and_prepare(grid_size=6, image_path=plan_observe_path)
            print(f"截图已保存: {image_path}")
            print(f"网格信息: {grid_info}")

            plan_prompt = build_plan_prompt(
                user_command=command,
                grid_size=int(grid_info.get("grid_size", 6)),
                cell_width=float(grid_info.get("cell_width", 0.0)),
                cell_height=float(grid_info.get("cell_height", 0.0)),
                max_plan_steps=MAX_PLAN_STEPS,
                skill_catalog=skill_catalog,
                skill_guidance=active_skill.plan_guidance() if active_skill else "",
                memory_guidance=memory_guidance,
            )
            print(f"\n发送给 LLM 的 Plan Prompt (长度: {len(plan_prompt)} 字符):")
            print("-" * 40)
            print(plan_prompt[:500] + "..." if len(plan_prompt) > 500 else plan_prompt)
            print("-" * 40)

            print("\n正在调用 LLM (qwen-vl) 生成计划...")
            plan_text = call_llm_with_image(plan_prompt, image_path)
            print(f"LLM Plan 输出:\n{plan_text[:300]}..." if len(plan_text) > 300 else f"LLM Plan 输出:\n{plan_text}")

            parsed_plan, error_msg = parse_plan(plan_text)
            if not parsed_plan:
                print(f"计划解析失败: {error_msg}，使用兜底计划")
                parsed_plan = [{"action": "wait", "seconds": 1, "reason": "兜底等待"}, {"action": "done"}]
            plan = normalize_plan(parsed_plan, max_plan_steps=MAX_PLAN_STEPS)

            print(f"\n解析后的计划 (共 {len(plan)} 步):")
            for i, step in enumerate(plan, 1):
                print(f"  {i}. {step.get('action')}: {step.get('reason', '')}")

            yield {
                'type': 'step',
                'data': {
                    'thought': f"计划生成完成，共 {len(plan)} 步",
                    'action': None,
                    'action_reason': None,
                    'screenshot_base64': encode_image_to_base64(image_path),
                    'done': False,
                    'skill_info': {
                        'name': skill_name,
                        'stage': active_skill.stage if active_skill else None,
                        'enforced': False,
                        'original_action': None,
                    }
                }
            }

            # ReAct 阶段
            print("\n" + "=" * 60)
            print("【ReAct 阶段】开始执行...")
            print("=" * 60)

            history = []
            finished = False

            for step_index in range(1, MAX_REACT_STEPS + 1):
                print(f"\n{'=' * 60}")
                print(f"【步骤 {step_index}/{MAX_REACT_STEPS}】")
                print(f"{'=' * 60}")

                before_path = os.path.join(capture_dir, f"step-{step_index:02d}-observe.png")
                img_path, latest_grid_info = capture_and_prepare(grid_size=6, image_path=before_path)
                print(f"截图: {img_path}")

                react_prompt = build_react_prompt(
                    user_command=command,
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

                print(f"\n发送给 LLM 的 ReAct Prompt (长度: {len(react_prompt)} 字符):")
                print("-" * 40)
                print(react_prompt[:800] + "...(截断)" if len(react_prompt) > 800 else react_prompt)
                print("-" * 40)

                print("\n正在调用 LLM (qwen-vl + tools)...")
                tool_call = call_llm_with_image_and_tools(
                    prompt=react_prompt,
                    image_path=img_path,
                    tools=REACT_FUNCTION_TOOLS,
                )

                print(f"\nLLM 原始响应 (tool_call):")
                print("-" * 40)
                print(json.dumps(tool_call, ensure_ascii=False, indent=2) if tool_call else "None")
                print("-" * 40)

                action = action_from_tool_call(tool_call)
                original_action_type = str(action.get("action", ""))

                # Apply skill enforcement if active_skill exists
                enforced = False
                if active_skill:
                    enforced_action = active_skill.enforce_action(action)
                    if enforced_action != action:
                        print(f"\n[Skill 约束] 原始 action 被修改:")
                        print(f"  原: {action}")
                        print(f"  新: {enforced_action}")
                        enforced = True
                        original_action_type = str(action.get("action", ""))
                    action = normalize_action(enforced_action)

                action_type = str(action.get("action", ""))
                action_reason = str(action.get("reason", ""))

                skill_stage_info = f" (skill stage: {active_skill.stage})" if active_skill else " (无技能)"
                print(f"\n决策结果: {action_type}")
                print(f"执行原因: {action_reason}")
                print(f"{skill_stage_info}")

                # Yield step result with full info
                yield {
                    'type': 'step',
                    'data': {
                        'thought': f"{action_type}: {action_reason}",
                        'action': action_type,
                        'action_reason': action_reason,
                        'screenshot_base64': encode_image_to_base64(img_path),
                        'done': False,
                        'raw_tool_call': tool_call,
                        'skill_info': {
                            'name': skill_name,
                            'stage': active_skill.stage if active_skill else None,
                            'enforced': enforced,
                            'original_action': original_action_type if enforced else None,
                        }
                    }
                }

                if action_type == "done":
                    if active_skill and not active_skill.allow_done():
                        print("  技能流程未完成，忽略 done 并继续。")
                        continue
                    print("\n✓ LLM 判定任务完成")
                    finished = True
                    break

                print(f"\n执行动作: {action_type}")
                from app.agent import execute_action
                success = execute_action(action, latest_grid_info)
                history.append({"action": action, "success": success})
                print(f"执行结果: {'成功' if success else '失败'}")

                # Update skill stage after action execution
                if active_skill:
                    old_stage = active_skill.stage
                    active_skill.on_action_result(action, success)
                    if old_stage != active_skill.stage:
                        print(f"\n[Skill] 阶段更新: {old_stage} → {active_skill.stage}")

                if not success:
                    print("执行失败，记录到历史并继续下一轮")

                print(f"历史记录数: {len(history)}")
                await asyncio.sleep(0.5)

            print("\n" + "=" * 60)
            if finished:
                print(f"【任务完成】共执行 {len(history)} 步")
            else:
                print(f"【任务结束】达到最大轮次 {MAX_REACT_STEPS}，共执行 {len(history)} 步")
            print("=" * 60)

            yield {
                'type': 'done',
                'data': f"执行完成，共 {len(history)} 步" if finished else "达到最大轮次"
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[Bridge] Error: {e}")
            yield {'type': 'error', 'data': str(e)}


bridge = AgentBridge()