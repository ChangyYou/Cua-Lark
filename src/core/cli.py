"""
核心模块 - 命令行接口

提供 cua-lark 命令行工具。
"""

import argparse
import sys
import os

# 添加项目根目录到路径（支持安装后运行）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="CUA-Lark: 基于多模态大模型的飞书桌面端智能操作代理"
    )
    parser.add_argument(
        "command",
        type=str,
        nargs="*",
        help="要执行的自然语言命令，如 '帮我给游畅发送你好'"
    )
    parser.add_argument(
        "--grid-size", "-g",
        type=int,
        default=6,
        help="网格大小（默认6x6）"
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="开启调试模式"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        print("\n示例:")
        print("  cua-lark 帮我给游畅发送你好")
        print("  cua-lark -g 8 给王经理发消息说后端联调已经跑通了")
        return

    # 将命令拼接成字符串
    user_command = "".join(args.command)
    print(f"收到命令: {user_command}")

    # 导入并运行 Agent
    from src.core.agent import run_agent
    run_agent(user_command, grid_size=args.grid_size, debug=args.debug)


if __name__ == "__main__":
    main()
