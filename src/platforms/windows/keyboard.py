"""
Windows keyboard/text input helpers.
"""

import time

import pyautogui
import pyperclip


def paste_text(text: str, hwnd: int = None) -> None:
    """Paste text through the clipboard to support non-ASCII input."""
    if hwnd:
        from platforms.windows.click import ensure_window_active
        ensure_window_active(hwnd)
        time.sleep(0.1)
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")
    print(f"粘贴文本: {text}")


def type_english(text: str, interval: float = 0.05, hwnd: int = None) -> None:
    """Type ASCII text directly."""
    if hwnd:
        from platforms.windows.click import ensure_window_active
        ensure_window_active(hwnd)
        time.sleep(0.1)
    pyautogui.write(text, interval=interval)
    print(f"输入英文: {text}")


def input_message(text: str, hwnd: int = None) -> None:
    """Choose between direct typing and clipboard paste automatically."""
    if any(ord(char) > 127 for char in text):
        paste_text(text, hwnd)
    else:
        type_english(text, interval=0.05, hwnd=hwnd)


if __name__ == "__main__":
    print("测试输入中文...")
    time.sleep(1)
    input_message("你好")

