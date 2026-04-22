"""
Function-calling tool schemas.
"""

REACT_FUNCTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "click_position",
            "description": "使用原生坐标定位直接点击目标元素。通过此工具直接返回目标元素在整个屏幕/窗口中的相对坐标比例（0.000 到 1.000）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "x_ratio": {
                        "type": "number",
                        "description": "目标元素在横向的相对位置（0.000代表最左侧，1.000代表最右侧，例如 0.532）",
                    },
                    "y_ratio": {
                        "type": "number",
                        "description": "目标元素在纵向的相对位置（0.000代表最顶部，1.000代表最底部，例如 0.871）",
                    },
                    "reason": {
                        "type": "string",
                        "description": "为什么点击这个绝对坐标位置",
                    },
                },
                "required": ["x_ratio", "y_ratio"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "按下按键。支持 enter / return / command+k / cmd+k / ctrl+k。",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "按键名称",
                    },
                    "reason": {
                        "type": "string",
                        "description": "为什么按这个键",
                    },
                },
                "required": ["key"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "paste_content",
            "description": "将内容粘贴到当前输入区域。",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要粘贴的文本",
                    },
                    "reason": {
                        "type": "string",
                        "description": "为什么粘贴这段文本",
                    },
                },
                "required": ["text"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scroll",
            "description": "滚动鼠标滚轮。向下滚动查看更多内容使用负数（如 -500），向上滚动使用正数（如 500）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "integer",
                        "description": "滚动的量。负数表示向下滚动（查看下方内容），正数表示向上滚动（查看上方内容）。建议单次滚动量在 300 到 800 之间。",
                    },
                    "reason": {
                        "type": "string",
                        "description": "为什么需要滚动屏幕",
                    },
                },
                "required": ["amount", "reason"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "done",
            "description": "当且仅当确定当前用户指令的目标已经完全达成时调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "为什么认为任务已经完成",
                    },
                },
                "required": ["reason"],
                "additionalProperties": False,
            },
        },
    },
]

SKILL_ROUTER_FUNCTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "activate_skill",
            "description": "当用户目标满足某个 skill 触发条件时，激活该 skill。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "skill 名称（与 catalog 保持一致）"},
                    "reason": {"type": "string", "description": "触发原因"},
                },
                "required": ["name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "skip_skill",
            "description": "当不存在匹配 skill 时，显式跳过。",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "跳过原因"},
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
]
