"""
Windows screen capture implementation.
"""

import mss
import win32gui
from PIL import Image

from platforms.common.grid import grid_to_absolute_coordinates
from platforms.common.screen import add_grid_overlay, build_grid_info


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
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                window_list.append((hwnd, title))

    def list_all_windows(self) -> list:
        """List visible windows for debugging purposes."""
        window_list = []
        win32gui.EnumWindows(self._enum_windows_callback, window_list)
        return window_list

    def find_lark_window(self) -> dict | None:
        """Find the current Lark desktop window."""
        window_list = []
        win32gui.EnumWindows(self._enum_windows_callback, window_list)
        lark_windows = [(hwnd, title) for hwnd, title in window_list if "飞书" in title]

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

    def add_grid_overlay(self, image: Image.Image) -> Image.Image:
        """Annotate the screenshot with a numeric grid."""
        return add_grid_overlay(image, self.grid_size, WINDOWS_FONT_CANDIDATES)

    def capture_with_grid(self, window_rect: dict | None = None) -> tuple[Image.Image, dict]:
        """Capture a window and return the annotated image plus grid metadata."""
        image = self.capture_window(window_rect)
        image_with_grid = self.add_grid_overlay(image)
        grid_info = build_grid_info(self.grid_size, image, self.window_info)
        return image_with_grid, grid_info

    def grid_to_coordinates(self, grid_number: int, grid_info: dict) -> tuple[int, int]:
        """Return the absolute coordinates of the given grid cell center."""
        return grid_to_absolute_coordinates(grid_number, grid_info, offset_ratio=0.5)


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

