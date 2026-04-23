"""
Windows screen capture implementation.
"""

import mss
import win32gui
from PIL import Image

from platforms.common.screen import build_grid_info


WINDOWS_FONT_CANDIDATES = [
    "arial.ttf",
]


class ScreenCapture:
    """Capture the Lark window and annotate it with a grid."""

    def __init__(self, grid_size: int = 6):
        self.grid_size = grid_size
        self.sct = mss.mss()
        self.window_info = None
        self._lark_hwnd = None

    def _enum_windows_callback(self, hwnd, window_list) -> None:
        title = win32gui.GetWindowText(hwnd)
        # 为了避免把完全不可见的后台隐藏窗口（比如托盘后台进程）拉出来，
        # 我们还是需要保证它至少有 WS_VISIBLE 属性，或者它被最小化了。
        # 纯隐藏窗口（即没有显示过的）在 Windows 下很难被强行画出来。
        if title and (win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd)):
            window_list.append((hwnd, title))

    def list_all_windows(self) -> list:
        """List visible windows for debugging purposes."""
        window_list = []
        win32gui.EnumWindows(self._enum_windows_callback, window_list)
        return window_list

    def find_lark_window(self) -> dict | None:
        """Find the current Lark desktop window."""
        import win32process
        import win32con
        
        window_list = []
        win32gui.EnumWindows(self._enum_windows_callback, window_list)
        # 过滤掉常见的后台不可见窗口
        lark_windows = []
        for hwnd, title in window_list:
            if "飞书" in title:
                # GetWindowRect 如果返回 (0,0,0,0) 说明这是一个纯后台服务窗口，不能用来截图
                rect = win32gui.GetWindowRect(hwnd)
                if rect[2] - rect[0] > 0 and rect[3] - rect[1] > 0:
                    lark_windows.append((hwnd, title))

        # 如果还是找不到可见或最小化的飞书，尝试通过快捷方式拉起
        if not lark_windows:
            print("未找到任何飞书窗口！尝试从快捷方式拉起...")
            import os
            import time
            
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            public_desktop = r"C:\Users\Public\Desktop"
            
            shortcut_found = False
            for d_path in [desktop_path, public_desktop]:
                if os.path.exists(d_path):
                    for f in os.listdir(d_path):
                        if "飞书" in f and f.endswith(".lnk"):
                            shortcut_path = os.path.join(d_path, f)
                            print(f"找到桌面快捷方式: {shortcut_path}，正在拉起...")
                            os.startfile(shortcut_path)
                            shortcut_found = True
                            break
                if shortcut_found:
                    break
                    
            if not shortcut_found:
                print("未能找到飞书可执行文件或快捷方式，请手动打开飞书主界面！")
            
            # 给予充足的时间让它从后台加载 UI
            time.sleep(3.0)
            
            # 重新扫描
            fallback_list = []
            win32gui.EnumWindows(self._enum_windows_callback, fallback_list)
            for hwnd, title in fallback_list:
                if "飞书" in title:
                    class_name = win32gui.GetClassName(hwnd)
                    if "Tray" in class_name or "Notify" in class_name:
                        continue
                    rect = win32gui.GetWindowRect(hwnd)
                    if rect[2] - rect[0] > 100 and rect[3] - rect[1] > 100:
                        lark_windows.append((hwnd, title))
                        break

        if not lark_windows:
            print("未找到飞书窗口！当前部分窗口：")
            for _, title in window_list[:20]:
                print(f"  - {title}")

            monitors = self.sct.monitors
            monitor = monitors[1] if len(monitors) > 1 else monitors[0]
            self.window_info = {
                "left": monitor["left"],
                "top": monitor["top"],
                "width": monitor["width"],
                "height": monitor["height"],
            }
            return self.window_info

        self._lark_hwnd, title = lark_windows[0]
        
        # 方案一：根据主窗口PID查找同进程下的最顶层可见窗口（如预约会议弹窗）
        _, pid = win32process.GetWindowThreadProcessId(self._lark_hwnd)
        
        def find_top_window_for_pid(hwnd, top_windows):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                _, hwnd_pid = win32process.GetWindowThreadProcessId(hwnd)
                if hwnd_pid == pid:
                    # 过滤掉面积太小或者不可交互的窗口
                    rect = win32gui.GetWindowRect(hwnd)
                    if rect[2] - rect[0] > 100 and rect[3] - rect[1] > 100:
                        top_windows.append(hwnd)
        
        pid_windows = []
        win32gui.EnumWindows(find_top_window_for_pid, pid_windows)
        
        if pid_windows:
            # EnumWindows 返回的列表默认是按 Z-order 从顶层到底层排列的
            self._lark_hwnd = pid_windows[0]
            title = win32gui.GetWindowText(self._lark_hwnd)
        
        # 核心修复：唤醒后台或最小化的飞书进程
        # 很多时候，即使用 SW_SHOW，窗口如果不处于激活状态，鼠标点击也会被吃掉
        win32gui.ShowWindow(self._lark_hwnd, win32con.SW_SHOW)
        
        if win32gui.IsIconic(self._lark_hwnd):
            win32gui.ShowWindow(self._lark_hwnd, win32con.SW_RESTORE)
            
        try:
            # 强制挂载输入焦点，防止点击失效
            win32gui.SetForegroundWindow(self._lark_hwnd)
            win32gui.BringWindowToTop(self._lark_hwnd)
        except Exception:
            pass
            
        print(f"找到飞书窗口: {title} (hwnd: {self._lark_hwnd})")

        left, top, right, bottom = win32gui.GetClientRect(self._lark_hwnd)
        client_left, client_top = win32gui.ClientToScreen(self._lark_hwnd, (left, top))
        client_right, client_bottom = win32gui.ClientToScreen(self._lark_hwnd, (right, bottom))

        self.window_info = {
            "left": client_left,
            "top": client_top,
            "width": client_right - client_left,
            "height": client_bottom - client_top,
            "title": title,
            "hwnd": self._lark_hwnd,
        }
        return self.window_info

    def capture_window(self, window_rect: dict | None = None) -> Image.Image:
        """Capture the given window rect or the current Lark window."""
        window_rect = window_rect or self.find_lark_window()
        if window_rect is None:
            raise RuntimeError("无法找到飞书窗口")

        self.window_info = window_rect
        screenshot = self.sct.grab(window_rect)
        return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")



    def capture_with_grid(self, window_rect: dict | None = None) -> tuple[Image.Image, dict]:
        """Capture a window and return the annotated image plus grid metadata."""
        image = self.capture_window(window_rect)
        grid_info = build_grid_info(self.grid_size, image, self.window_info)
        return image, grid_info




def capture_lark_window(grid_size: int = 6) -> tuple[Image.Image, dict]:
    """Convenience helper to capture the current Lark window with grid overlay."""
    capture = ScreenCapture(grid_size=grid_size)
    window_rect = capture.find_lark_window()
    return capture.capture_with_grid(window_rect)


if __name__ == "__main__":
    import os

    print("截取飞书窗口...")
    image, grid_info = capture_lark_window()
    print(f"截图尺寸: {grid_info['image_width']}x{grid_info['image_height']}")
    print(f"网格大小: {grid_info['grid_size']}x{grid_info['grid_size']}")
    print(f"单元格尺寸: {grid_info['cell_width']:.1f}x{grid_info['cell_height']:.1f}")
    os.makedirs("captures", exist_ok=True)
    image.save("captures/lark_capture.png")
    print("截图已保存到 captures/lark_capture.png")

