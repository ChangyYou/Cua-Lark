"""
Utility script for local skill debugging.

Usage:
    python skills/send-message/scripts/run.py "帮我给游畅发送你好"
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    src_root = os.path.join(project_root, "src")
    if src_root not in sys.path:
        sys.path.insert(0, src_root)

    from app.skills.send_message import SendMessageSkill  # pylint: disable=import-outside-toplevel

    command = "".join(sys.argv[1:]).strip()
    if not command:
        print("用法: python skills/send-message/scripts/run.py <命令>")
        return 1

    skill = SendMessageSkill.try_create(command)
    if not skill:
        print("未命中 send-message skill")
        return 0

    print("命中 skill: send-message")
    print(f"联系人: {skill.recipient}")
    print(f"消息: {skill.message}")
    print("Plan Guidance:")
    print(skill.plan_guidance())
    print("ReAct Guidance:")
    print(skill.react_guidance())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
