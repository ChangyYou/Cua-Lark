"""
macOS keyboard/text input helpers.
"""

import time

import Quartz
import pyperclip

from platforms.macos.hotkey import hotkey


def paste_text(text: str) -> None:
    """Paste text through the clipboard to support non-ASCII input."""
    pyperclip.copy(text)
    hotkey("command", "v")
    print(f"粘贴文本：{text}")


def type_english(text: str, interval: float = 0.05) -> None:
    """Type ASCII text by posting keyboard events."""
    for char in text:
        key_down = Quartz.CGEventCreateKeyboardEvent(None, 0, True)
        Quartz.CGEventKeyboardSetUnicodeString(key_down, len(char), char)
        key_up = Quartz.CGEventCreateKeyboardEvent(None, 0, False)
        Quartz.CGEventKeyboardSetUnicodeString(key_up, len(char), char)

        Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_down)
        time.sleep(interval)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_up)

    print(f"输入英文：{text}")


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

