"""
Long-term memory module for CUA-Lark.
Extracts reusable knowledge from execution history and stores it for future use.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.utils.llm import call_llm_with_text_and_tools

MEMORY_FILE_PATH = Path(__file__).resolve().parents[3] / "data" / "memory.json"

def _ensure_memory_file() -> None:
    MEMORY_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE_PATH.exists():
        with open(MEMORY_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def load_memories() -> list[dict[str, Any]]:
    """Load all stored memories."""
    _ensure_memory_file()
    try:
        with open(MEMORY_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"读取记忆文件失败: {e}")
        return []

def save_memory(content: str) -> None:
    """Save a new memory entry."""
    memories = load_memories()
    new_memory = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "content": content
    }
    memories.append(new_memory)
    try:
        with open(MEMORY_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)
        print(f"\n  [Memory] 成功保存长期记忆: {content}")
    except Exception as e:
        print(f"\n  [Memory] 保存记忆文件失败: {e}")

def extract_and_store_memory(user_command: str, history_text: str, success: bool) -> None:
    """Analyze execution history and extract valuable knowledge into memory."""
    print("\n  [Memory] 正在分析本次执行是否产生有价值的长期记忆...")
    
    prompt = f"""你是一个桌面操作智能体的反思模块。
刚才智能体执行了一个任务。请分析执行历史，判断是否发现了关于飞书客户端 UI 布局、特定操作范式、或者需要规避的错误的**通用长期知识**。
如果不具有通用性（比如只是一次普通的点击发送），则不要提取。
如果有，请提取为一条精炼的规则或知识（纯文本，不要超过100字）。

用户目标：{user_command}
任务是否最终成功：{"是" if success else "否"}

执行历史：
{history_text}

规则：
- 如果没有值得记忆的通用知识，不要调用工具，直接返回文字“无”。
- 如果有值得记忆的通用知识，必须调用 `store_memory` 工具，并传入 `content` 参数。
"""
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "store_memory",
                "description": "存储具有长期复用价值的知识",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "提取出的精炼规则或知识",
                        }
                    },
                    "required": ["content"],
                    "additionalProperties": False,
                },
            },
        }
    ]
    
    try:
        tool_call = call_llm_with_text_and_tools(prompt=prompt, tools=tools)
        if tool_call and tool_call.get("name") == "store_memory":
            content = tool_call.get("arguments", {}).get("content")
            if content:
                save_memory(content)
        else:
            print("  [Memory] 本次执行无新增长期记忆。")
    except Exception as e:
        print(f"  [Memory] 提取记忆时发生错误: {e}")

def get_memory_guidance() -> str:
    """Format stored memories for prompt injection."""
    memories = load_memories()
    if not memories:
        return ""
    
    lines = ["\n[长期记忆（经验参考）]："]
    for i, m in enumerate(memories, 1):
        lines.append(f"{i}. {m.get('content')}")
    return "\n".join(lines)
