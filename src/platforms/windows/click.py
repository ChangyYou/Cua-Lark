"""
Windows mouse interaction helpers.
"""

import time

import pyautogui

from platforms.common.grid import grid_to_absolute_coordinates
from platforms.windows.screen import ScreenCapture


def click_at(x: int, y: int) -> None:
    """Click at an absolute screen coordinate."""
    pyautogui.click(x, y)
    print(f"点击坐标: ({x}, {y})")


def click_grid(grid_number: int, grid_info: dict) -> None:
    """Click the center of a grid cell."""
    x, y = grid_to_absolute_coordinates(grid_number, grid_info)
    click_at(x, y)


def click_and_wait(grid_number: int, grid_info: dict, wait: float = 1.0) -> None:
    """Click a grid cell and wait for the UI to respond."""
    click_grid(grid_number, grid_info)
    time.sleep(wait)


def click_grid_bottom(grid_number: int, grid_info: dict, offset_ratio: float = 0.8) -> None:
    """Click near the bottom area of a grid cell."""
    x, y = grid_to_absolute_coordinates(grid_number, grid_info, offset_ratio=offset_ratio)
    click_at(x, y)
    print(f"点击坐标(下边界): ({x}, {y})")


if __name__ == "__main__":
    print("截取飞书窗口...")
    capture = ScreenCapture(grid_size=6)
    image, grid_info = capture.capture_with_grid()
    image.save("captures/test_click.png")

    print(f"截图尺寸: {grid_info['image_width']}x{grid_info['image_height']}")
    print(f"窗口位置: left={grid_info['window_info']['left']}, top={grid_info['window_info']['top']}")
    print(f"网格大小: {grid_info['grid_size']}x{grid_info['grid_size']}")
    print(f"单元格尺寸: {grid_info['cell_width']:.1f}x{grid_info['cell_height']:.1f}")

    print("2 秒后开始点击网格 23...")
    time.sleep(2)
    click_grid(23, grid_info)

