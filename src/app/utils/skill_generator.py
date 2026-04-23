"""
Skill generator module.
Automatically generates new skills from successful fallback executions.
"""

from __future__ import annotations

import os
from pathlib import Path

from app.utils.llm import call_llm_with_text_and_tools

SKILLS_ROOT = Path(__file__).resolve().parents[3] / "skills"

def analyze_and_generate_skill(user_command: str, history_text: str) -> None:
    """Analyze execution history and generate a new skill if valuable."""
    print("\n  [Skill Generator] 正在分析是否可以提炼为新的可复用 Skill...")

    prompt = f"""你是一个高级智能体架构师。刚才你的系统成功完成了一个“通用执行”任务。
请分析以下执行历史，判断该任务是否属于**高频、结构化、多步骤固定链路**的任务（例如发送指定格式的消息、创建日程等）。
如果只是一次极简单的点击，或者无法被泛化为固定技能，请返回“无”。
如果值得被固化为 Skill，请生成一个新 Skill。

用户目标：{user_command}

执行历史：
{history_text}

规则：
- 必须调用 `generate_skill` 工具。
- 如果不值得生成，请在 `is_valuable` 传 false。
- 如果值得生成，请在 `is_valuable` 传 true，并提供 skill_name（如 `create-event`）、description、trigger_condition（正则表达式，用于匹配此类指令）以及符合 AgentSkill 协议的完整 Python 代码。
- 你的 Python 代码必须包含：
  1. `SKILL_DIR = Path(__file__).resolve().parents[1]`
  2. `load_skill_doc()` 函数读取 `SKILL.md`
  3. `[Name]Skill` 类实现 `AgentSkill` 协议，并支持简单的阶段状态机来控制执行链路（如 STAGE_0, STAGE_1...）。
  4. `describe_[name]_skill()` 返回字典。
"""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "generate_skill",
                "description": "生成新的可复用技能代码",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "is_valuable": {
                            "type": "boolean",
                            "description": "是否值得提炼为 Skill"
                        },
                        "skill_name": {
                            "type": "string",
                            "description": "技能的名称，短横线命名法（如 create-event）"
                        },
                        "description": {
                            "type": "string",
                            "description": "技能的简短英文描述"
                        },
                        "trigger_condition": {
                            "type": "string",
                            "description": "用于匹配此类指令的 Python 正则表达式"
                        },
                        "python_code": {
                            "type": "string",
                            "description": "完整的符合 AgentSkill 协议的 Python 代码"
                        }
                    },
                    "required": ["is_valuable"],
                    "additionalProperties": False,
                },
            },
        }
    ]

    try:
        tool_call = call_llm_with_text_and_tools(prompt=prompt, tools=tools)
        if tool_call and tool_call.get("name") == "generate_skill":
            args = tool_call.get("arguments", {})
            if args.get("is_valuable"):
                skill_name = args.get("skill_name")
                description = args.get("description")
                python_code = args.get("python_code")
                
                if skill_name and python_code:
                    _write_skill_to_disk(skill_name, description, python_code)
            else:
                print("  [Skill Generator] 本次执行不具备结构化特征，跳过 Skill 生成。")
        else:
            print("  [Skill Generator] 未生成新 Skill。")
    except Exception as e:
        print(f"  [Skill Generator] 技能生成时发生错误: {e}")

def _write_skill_to_disk(skill_name: str, description: str, python_code: str) -> None:
    """Write the generated skill files to disk."""
    skill_dir = SKILLS_ROOT / skill_name
    scripts_dir = skill_dir / "scripts"
    
    scripts_dir.mkdir(parents=True, exist_ok=True)
    
    # Write SKILL.md
    skill_md_path = skill_dir / "SKILL.md"
    skill_md_content = f"""---
name: {skill_name}
description: "{description}"
---
这是系统自动根据成功执行经验生成的技能。
"""
    skill_md_path.write_text(skill_md_content, encoding="utf-8")
    
    # Write python script
    module_name = skill_name.replace("-", "_")
    script_path = scripts_dir / f"{module_name}.py"
    script_path.write_text(python_code, encoding="utf-8")
    
    print(f"\n  [Skill Generator] 🎉 成功生成并注册新技能: {skill_name}")
    print(f"  [Skill Generator] 代码已保存至: {script_path}")
