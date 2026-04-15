"""
执行层 - 快捷键模块

模拟键盘快捷键操作。
"""

import win32gui
import win32con
import pyautogui
import time


def activate_window(hwnd: int) -> None:
    """
    激活指定窗口（将其置于前台）

    Args:
        hwnd: 窗口句柄
    """
    # 先尝试正常激活
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.3)
    print(f"已激活窗口 hwnd: {hwnd}")


def press(key: str) -> None:
    """
    按下单个键

    Args:
        key: 键名，如 'enter', 'esc', 'k' 等
    """
    pyautogui.press(key)
    print(f"按键: {key}")


def hotkey(*keys) -> None:
    """
    按下组合键

    Args:
        *keys: 键名列表，如 'ctrl', 'k' 表示 Ctrl+K
    """
    pyautogui.hotkey(*keys)
    print(f"组合键: {'+'.join(keys)}")


def type_text(text: str, interval: float = 0.05) -> None:
    """
    输入英文文本（逐字输入）

    Args:
        text: 要输入的文本
        interval: 每个字符之间的间隔（秒）
    """
    pyautogui.write(text, interval=interval)
    print(f"输入文本: {text}")


def open_search(hwnd: int = None) -> None:
    """
    打开飞书搜索框（Ctrl+K）

    Args:
        hwnd: 窗口句柄，如果提供则先激活窗口
    """
    if hwnd:
        activate_window(hwnd)
    hotkey('ctrl', 'k')
    time.sleep(0.5)


def send_message() -> None:
    """发送消息（回车）"""
    press('enter')


def delete_text(count: int = 1) -> None:
    """删除文本"""
    for _ in range(count):
        pyautogui.press('backspace')
        time.sleep(0.05)


if __name__ == "__main__":
    # 测试快捷键
    print("测试：按 Ctrl+K...")
    time.sleep(1)
    open_search()
