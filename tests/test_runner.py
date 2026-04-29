import os
import sys
import time
import pytest

# Ensure the app module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app.agent import run_agent, capture_and_prepare
from app.utils.asserter import analyze_assertion

def test_cua_lark_scenario(test_case):
    """
    Execute a single test case driven by CUA-Lark agent and verify with Assertion Agent.
    """
    suite_name = test_case["suite_name"]
    case = test_case["case"]
    
    case_id = case["id"]
    name = case["name"]
    steps = case["steps"]
    assert_condition = case.get("assert_condition")
    
    print(f"\n--- 正在执行测试用例: {suite_name} - {case_id} ({name}) ---")
    print(f"步骤: {steps}")
    
    # 1. 前置准备 (Setup)
    # 可以通过系统 API 将飞书强制拉到前台
    
    # 2. 执行期 (Execution)
    # 调用 CUA-Lark Agent，传入 steps 作为 user_command
    finished, final_image_path = run_agent(steps, debug=False)
    
    # 3. 断言期 (Verification)
    # 强制等待 UI 动画结束
    time.sleep(2.0)
    
    if assert_condition:
        print(f"\n开始视觉断言: {assert_condition}")
        
        # 截取当前全屏进行断言
        assert_image_path, _ = capture_and_prepare(grid_size=0, image_path=f"captures/assert_{case_id}.jpg")
        
        # 调用 Assertion Agent
        result = analyze_assertion(assert_condition, assert_image_path)
        
        # 为了 pytest-html 报告记录信息
        pytest.last_assert_image = assert_image_path
        pytest.last_assert_reason = result.get("reason", "No reason provided by Assertion Agent")
        
        assert result.get("passed", False) is True, f"视觉断言失败: {result.get('reason')}"
    
    # 如果没有断言条件，至少检查 Agent 是否正常跑完
    assert finished, f"Agent 未能完成所有步骤，在达到最大轮次前退出。用例: {case_id}"
    
    # 4. 恢复期 (Teardown & Clean up)
    # 这里可以添加退回主界面等清理逻辑，例如:
    # from platforms import press
    # press("esc")
