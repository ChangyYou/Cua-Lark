"""
执行层 - 键盘输入模块

处理中英文文本输入，中文使用剪贴板粘贴。
"""

import pyperclip
import pyautogui
import time


def paste_text(text: str) -> None:
    """
    粘贴文本（通过剪贴板，支持中文）

    Args:
        text: 要粘贴的文本
    """
    # 先复制到剪贴板
    pyperclip.copy(text)
    # 然后 Ctrl+V 粘贴
    pyautogui.hotkey('ctrl', 'v')
    print(f"粘贴文本: {text}")


def type_english(text: str, interval: float = 0.05) -> None:
    """
    输入英文文本（逐字输入）

    Args:
        text: 要输入的英文文本
        interval: 每个字符之间的间隔（秒）
    """
    pyautogui.write(text, interval=interval)
    print(f"输入英文: {text}")


def input_message(text: str) -> None:
    """
    输入消息（自动判断中英文）

    Args:
        text: 要输入的消息
    """
    # 判断是否包含非ASCII字符（中文）
    if any(ord(c) > 127 for c in text):
        paste_text(text)
    else:
        type_english(text)


if __name__ == "__main__":
    # 测试
    print("测试输入中文...")
    time.sleep(1)
    input_message("你好")
