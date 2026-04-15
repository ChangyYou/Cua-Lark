#!/usr/bin/env python
"""
CUA-Lark 命令行入口

用法：
    python cua-lark.py 帮我给游畅发送你好
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.agent import run_agent

if __name__ == "__main__":
    # 获取命令行参数（去掉脚本本身）
    command = sys.argv[1:] if len(sys.argv) > 1 else []

    if not command:
        print("用法: python cua-lark.py <命令>")
        print("示例: python cua-lark.py 帮我给游畅发送你好")
        sys.exit(1)

    user_command = "".join(command)
    print(f"收到命令: {user_command}")
    run_agent(user_command)
