"""
Windows keyboard/text input helpers.
"""

import time

import pyautogui
import pyperclip


def paste_text(text: str) -> None:
    """Paste text through the clipboard to support non-ASCII input."""
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")
    print(f"粘贴文本: {text}")


def type_english(text: str, interval: float = 0.05) -> None:
    """Type ASCII text directly."""
    pyautogui.write(text, interval=interval)
    print(f"输入英文: {text}")


def input_message(text: str) -> None:
    """Choose between direct typing and clipboard paste automatically."""
    if any(ord(char) > 127 for char in text):
        paste_text(text)
    else:
        type_english(text)


if __name__ == "__main__":
    print("测试输入中文...")
    time.sleep(1)
    input_message("你好")

