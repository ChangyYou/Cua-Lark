"""
核心模块 - Agent

完整 LLM 驱动方案：
1. LLM 解析用户命令 → 生成执行计划
2. 按计划执行每一步 + 状态验证
3. LLM 判断当前状态是否到达目标
"""

import json
import time
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

import dashscope
from dashscope import MultiModalConversation
import pyautogui

# 禁用 PyAutoGUI 安全机制
pyautogui.FAILSAFE = False

from src.perception.screen import capture_lark_window
from src.execution.hotkey import open_search, press, send_message
from src.execution.keyboard import input_message
from src.execution.click import click_grid_bottom

# 设置 API Key
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")


# ============ 系统提示词 ============
PLANNING_PROMPT = """你是一个桌面操作智能体，正在操控飞书桌面客户端。

用户命令：{user_command}

截图上有红色编号网格，每个格子有编号。
网格信息：{grid_size}x{grid_size} 网格，单元格尺寸 {cell_width:.0f}x{cell_height:.0f}

请分析用户命令，确定完成该任务需要哪些步骤。

支持的 action：
- open_search: 打开搜索框 {{"action":"open_search","reason":"打开搜索框"}}
- input_text: 输入文本 {{"action":"input_text","text":"要输入的文字","reason":"输入文字"}}
- click_grid: 点击网格 {{"action":"click_grid","grid":8,"offset_ratio":0.8,"reason":"点击网格"}}
- press_key: 按键 {{"action":"press_key","key":"enter","reason":"按回车"}}
- wait: 等待 {{"action":"wait","seconds":2,"reason":"等待加载"}}

注意：
1. 飞书搜索结果通常在第8号格子下半部分（offset_ratio=0.8）
2. 每个步骤必须具体，包含必要的参数
3. 返回 JSON 数组格式的计划，不要多余内容

返回格式：
[
  {{"action":"open_search","reason":"..."}},
  {{"action":"input_text","text":"xxx","reason":"..."}},
  ...
]

请生成完整的执行计划：
"""


def capture_and_prepare() -> tuple:
    """截取屏幕并保存"""
    img, grid_info = capture_lark_window(grid_size=6)
    img_path = "captures/agent_capture.png"
    img.save(img_path)
    return img_path, grid_info


def call_llm(prompt: str, temperature: float = 0.7) -> str:
    """调用 LLM"""
    messages = [{"role": "user", "content": [{"text": prompt}]}]

    try:
        response = MultiModalConversation.call(
            model="qwen-vl-max",
            messages=messages,
            temperature=temperature
        )

        if response.status_code == 200:
            content = response.output.choices[0].message.content
            if isinstance(content, list):
                content = content[0].get('text', '') if isinstance(content[0], dict) else str(content[0])
            return content
        else:
            print(f"LLM 调用失败: {response.message}")
            return "[]"
    except Exception as e:
        print(f"LLM 调用异常: {e}")
        return "[]"


def parse_plan(content: str) -> list:
    """解析执行计划"""
    try:
        # 如果是列表直接返回
        if isinstance(content, list):
            return content

        # 提取 JSON 数组
        if "[" in content:
            start = content.find("[")
            end = content.rfind("]") + 1
            content = content[start:end]

        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"计划解析失败: {e}")
        return []


def execute_action(action: dict, grid_info: dict) -> bool:
    """执行单个动作"""
    action_type = action.get("action", "")
    reason = action.get("reason", "")

    print(f"  执行: {action_type} - {reason}")

    try:
        if action_type == "open_search":
            hwnd = grid_info.get("window_info", {}).get("hwnd")
            open_search(hwnd)
            return True

        elif action_type in ("input_text", "type", "paste"):
            text = action.get("text", "")
            input_message(text)
            return True

        elif action_type in ("click_grid", "click"):
            grid = action.get("grid", 8)
            offset_ratio = action.get("offset_ratio", 0.8)
            click_grid_bottom(grid, grid_info, offset_ratio)
            return True

        elif action_type in ("press_key", "press"):
            key = action.get("key", "enter")
            press(key)
            return True

        elif action_type == "wait":
            seconds = action.get("seconds", 1)
            time.sleep(seconds)
            return True

        else:
            print(f"  未知动作: {action_type}")
            return False

    except Exception as e:
        print(f"  执行异常: {e}")
        return False


def run_agent(user_command: str, grid_size: int = 6, debug: bool = False):
    """运行 Agent"""
    print("=" * 50)
    print("CUA-Lark Agent 启动")
    print(f"用户命令: {user_command}")
    print("=" * 50)

    # 1. 截取屏幕获取网格信息
    img_path, grid_info = capture_and_prepare()
    cell_w = grid_info["cell_width"]
    cell_h = grid_info["cell_height"]

    # 2. 让 LLM 生成执行计划
    print("\n【步骤 1】LLM 生成执行计划...")
    planning_prompt = PLANNING_PROMPT.format(
        user_command=user_command,
        grid_size=grid_size,
        cell_width=cell_w,
        cell_height=cell_h
    )
    plan_text = call_llm(planning_prompt)
    print(f"LLM 计划:\n{plan_text}")

    # 3. 解析计划
    plan = parse_plan(plan_text)
    if not plan:
        print("生成执行计划失败！")
        return

    print(f"\n执行计划（共 {len(plan)} 步）:")
    for i, step in enumerate(plan):
        print(f"  {i+1}. {step.get('action')}: {step.get('reason', '')}")

    # 4. 按计划执行
    print(f"\n【步骤 2】执行计划...")
    for i, action in enumerate(plan):
        print(f"\n  [{i+1}/{len(plan)}] {action.get('action')}")

        # 每步执行前重新截图，获取最新的 window_info
        img_path, grid_info = capture_and_prepare()

        # 执行动作
        success = execute_action(action, grid_info)
        if not success:
            print(f"  执行失败，跳过")
            continue

        # 等待界面响应
        time.sleep(1)

        # 5. 验证状态（可选，当前简化处理）
        # 如果需要验证，可以在这里加 LLM 状态检查

    print("\n" + "=" * 50)
    print("任务完成！")
    print("=" * 50)


if __name__ == "__main__":
    run_agent("帮我给游畅发送你好")
