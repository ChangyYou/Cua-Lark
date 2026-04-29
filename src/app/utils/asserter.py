"""
Assertion Agent: Visual verification engine for automated testing.
"""

from typing import Any
from app.utils.llm import call_llm_with_image_and_tools

ASSERT_TOOLS = [{
    "name": "submit_test_result",
    "description": "提交界面视觉测试验证结果",
    "parameters": {
        "type": "object",
        "properties": {
            "passed": {
                "type": "boolean",
                "description": "当前界面截图是否完全满足测试预期条件"
            },
            "evidence": {
                "type": "string",
                "description": "支持该判定结果的视觉证据说明，必须结合截图中的具体元素"
            }
        },
        "required": ["passed", "evidence"]
    }
}]

def verify_assertion(image_path: str, assertion_condition: str) -> dict[str, Any]:
    """
    使用视觉大模型对测试结果进行独立验证 (黑盒测试)。
    
    Args:
        image_path: 任务执行完毕后的最终屏幕截图路径
        assertion_condition: 测试用例中定义的期望断言条件
        
    Returns:
        dict 包含 'passed' (bool) 和 'evidence' (str)
    """
    prompt = f"""
    你是一个极其严谨的自动化测试 QA 工程师。
    请观察提供的应用最终状态截图，判断当前界面是否满足以下测试断言条件：
    
    【测试断言条件】：{assertion_condition}
    
    要求：
    1. 严谨客观：不要猜测截图外发生了什么，只根据截图【肉眼可见】的元素进行判断。
    2. 寻找证据：在判定成功前，你必须在画面中找到明确的文本、高亮状态、弹窗提示或图标作为证据。
    3. 容错性：如果存在遮挡、明显的错误弹窗或状态不符，即使部分符合预期，也应当判定为 passed=false。
    """
    
    tool_call = call_llm_with_image_and_tools(
        prompt=prompt,
        image_path=image_path,
        tools=ASSERT_TOOLS
    )
    
    if tool_call and tool_call.get("name") == "submit_test_result":
        return tool_call.get("arguments", {"passed": False, "evidence": "验证工具调用参数解析失败"})
        
    return {"passed": False, "evidence": "大模型未能返回结构化的验证结果"}
