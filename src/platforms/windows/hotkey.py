"""
Windows hotkey helpers.
"""

import time

import pyautogui
import win32con
import win32gui


def activate_window(hwnd: int) -> None:
    """Bring the target window to the foreground."""
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.3)
    print(f"已激活窗口 hwnd: {hwnd}")


def press(key: str) -> None:
    """Press a single key."""
    pyautogui.press(key)
    print(f"按键: {key}")


def hotkey(*keys) -> None:
    """Press a hotkey combination."""
    pyautogui.hotkey(*keys)
    print(f"组合键: {'+'.join(keys)}")


def open_search(window_info: dict | None = None) -> None:
    """Open the Lark search input with Ctrl+K."""
    hwnd = (window_info or {}).get("hwnd")
    if hwnd:
        activate_window(hwnd)
    hotkey("ctrl", "k")
    time.sleep(0.5)


def send_message() -> None:
    """Send the current message."""
    press("enter")


def delete_text(count: int = 1) -> None:
    """Delete characters with backspace."""
    for _ in range(count):
        pyautogui.press("backspace")
        time.sleep(0.05)


if __name__ == "__main__":
    print("测试：按 Ctrl+K...")
    time.sleep(1)
    open_search()

