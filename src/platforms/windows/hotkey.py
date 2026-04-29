"""
Windows hotkey helpers.
"""

import time

import pyautogui
import win32con
import win32gui


def activate_window(hwnd: int) -> None:
    """Bring the target window to the foreground."""
    from platforms.windows.click import ensure_window_active
    ensure_window_active(hwnd)
    time.sleep(0.3)
    print(f"已激活窗口 hwnd: {hwnd}")


def press(key: str) -> None:
    """Press a single key."""
    try:
        pyautogui.keyDown(key)
        time.sleep(0.05)
        pyautogui.keyUp(key)
        time.sleep(0.05)
        print(f"按键: {key}")
    except Exception as e:
        print(f"按键执行异常: {e}")


def hotkey(*keys) -> None:
    """Press a hotkey combination."""
    try:
        # 确保没有残留的修饰键卡住
        for k in ["ctrl", "shift", "alt"]:
            pyautogui.keyUp(k)
            
        for key in keys:
            pyautogui.keyDown(key)
            time.sleep(0.05)
        for key in reversed(keys):
            pyautogui.keyUp(key)
            time.sleep(0.05)
        print(f"组合键: {'+'.join(keys)}")
    except Exception as e:
        print(f"组合键执行异常: {e}")


def open_search(window_info: dict | None = None) -> None:
    """Open the Lark search input with Ctrl+K."""
    try:
        hwnd = (window_info or {}).get("hwnd")
        if hwnd:
            activate_window(hwnd)
            time.sleep(0.5)
            
            # 使用原生点击来确保窗口确实获得了焦点
            try:
                rect = win32gui.GetWindowRect(hwnd)
                # left, top, right, bottom
                # 点击顶部居中偏上的搜索栏位置，以防 ctrl+k 不生效，直接点击搜索框通常也是最稳的
                # 飞书全局搜索框通常在顶部正中
                width = rect[2] - rect[0]
                safe_x = rect[0] + width // 2
                safe_y = rect[1] + 25
                pyautogui.click(safe_x, safe_y)
                time.sleep(0.3)
            except Exception as click_e:
                print(f"尝试点击激活窗口时失败: {click_e}")
                
        # 确保系统按键没有卡住
        for key in ["ctrl", "shift", "alt", "win"]:
            pyautogui.keyUp(key)
            
        # 尝试使用分解动作，因为 hotkey 在某些应用里可能太快
        pyautogui.keyDown("ctrl")
        time.sleep(0.1)
        pyautogui.press("k")
        time.sleep(0.1)
        pyautogui.keyUp("ctrl")
        time.sleep(0.5)
        
        print("成功执行: ctrl+k")
    except Exception as e:
        print(f"open_search 异常: {e}")


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

