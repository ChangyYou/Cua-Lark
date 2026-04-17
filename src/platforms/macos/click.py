"""
macOS mouse interaction helpers.
"""

import time

import Quartz

from platforms.common.grid import grid_to_absolute_coordinates
from platforms.macos.screen import ScreenCapture


def click_at(x: int, y: int) -> None:
    """Click at an absolute screen coordinate."""
    screen_height = Quartz.CGDisplayPixelsHigh(Quartz.CGMainDisplayID())
    macos_y = screen_height - y

    move_event = Quartz.CGEventCreateMouseEvent(
        None,
        Quartz.kCGEventMouseMoved,
        (x, macos_y),
        Quartz.kCGMouseButtonLeft,
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, move_event)

    click_down = Quartz.CGEventCreateMouseEvent(
        None,
        Quartz.kCGEventLeftMouseDown,
        (x, macos_y),
        Quartz.kCGMouseButtonLeft,
    )
    click_up = Quartz.CGEventCreateMouseEvent(
        None,
        Quartz.kCGEventLeftMouseUp,
        (x, macos_y),
        Quartz.kCGMouseButtonLeft,
    )

    Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_down)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_up)

    print(f"点击坐标：({x}, {macos_y})")


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


if __name__ == "__main__":
    print("截取飞书窗口...")
    capture = ScreenCapture(grid_size=6)
    image, grid_info = capture.capture_with_grid()
    image.save("captures/test_click_macos.png")

    print(f"截图尺寸：{grid_info['image_width']}x{grid_info['image_height']}")
    print(f"网格大小：{grid_info['grid_size']}x{grid_info['grid_size']}")

    print("2 秒后开始点击网格 23...")
    time.sleep(2)
    click_grid(23, grid_info)

