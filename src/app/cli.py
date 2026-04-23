"""
Command-line entrypoint for CUA-Lark.
"""

import argparse

from app.agent import run_agent


def main() -> None:
    """CLI main function."""
    parser = argparse.ArgumentParser(
        description="CUA-Lark: 基于多模态大模型的飞书桌面端智能操作代理"
    )
    parser.add_argument(
        "command",
        type=str,
        nargs="*",
        help="要执行的自然语言命令，如 '帮我给游畅发送你好'",
    )
    parser.add_argument(
        "--grid-size",
        "-g",
        type=int,
        default=10,
        help="网格大小（默认 6x6）",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="开启调试模式",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        print("\n示例:")
        print("  cua-lark 帮我给游畅发送你好")
        print("  cua-lark -g 8 给王经理发消息说后端联调已经跑通了")
        return

    user_command = "".join(args.command)
    print(f"收到命令: {user_command}")
    run_agent(user_command, grid_size=args.grid_size, debug=args.debug)


if __name__ == "__main__":
    main()

