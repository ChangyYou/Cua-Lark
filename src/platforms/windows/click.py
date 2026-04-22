"""
Windows mouse interaction helpers.
"""

import time
import win32gui
import win32con

import pyautogui

from platforms.windows.screen import ScreenCapture

def ensure_window_active(hwnd):
    """确保目标窗口处于完全可交互状态"""
    if not hwnd:
        return
    try:
        # 如果窗口最小化，恢复它
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        
        # 强制将窗口挂载到前台并激活
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        
        # 模拟按下一次 Alt 键，这在 Windows 10/11 中是破解焦点防窃取的常用黑魔法
        import pywin32_system32 # noqa
        import win32api
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
        win32gui.SetForegroundWindow(hwnd)
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        
    except Exception as e:
        print(f"尝试激活窗口失败: {e}")

def click_at(x: int, y: int, hwnd: int = None) -> None:
    """Click at an absolute screen coordinate."""
    if hwnd:
        ensure_window_active(hwnd)
        time.sleep(0.1) # 等待焦点真正切换
    pyautogui.click(x, y)
    print(f"点击坐标: ({x}, {y})")

def scroll(amount: int, hwnd: int = None) -> None:
    """Scroll the mouse wheel. Positive amount scrolls up, negative scrolls down."""
    if hwnd:
        ensure_window_active(hwnd)
        time.sleep(0.1)
    pyautogui.scroll(amount)
    print(f"滚动鼠标: {amount}")

if __name__ == "__main__":
    pass

