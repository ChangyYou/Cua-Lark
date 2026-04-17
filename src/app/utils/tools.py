"""
Function-calling tool schemas.
"""

REACT_FUNCTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "click_region",
            "description": "点击当前截图中的某个区域。优先使用网格编号定位，禁止固定使用同一编号。",
            "parameters": {
                "type": "object",
                "properties": {
                    "grid": {
                        "type": "integer",
                        "description": "网格编号（从 1 开始）",
                    },
                    "offset_ratio": {
                        "type": "number",
                        "description": "在格子中的纵向偏移比例，默认 0.5（中心），0.2 更偏上，0.8 更偏下",
                    },
                    "reason": {
                        "type": "string",
                        "description": "为什么点击这里",
                    },
                },
                "required": ["grid"],
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
