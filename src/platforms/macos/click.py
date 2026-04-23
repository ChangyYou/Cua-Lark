"""
macOS mouse interaction helpers.
"""

import time

import Quartz

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


def scroll(amount: int) -> None:
    """Scroll the mouse wheel. Positive amount scrolls up, negative scrolls down."""
    # amount unit for Quartz is line. -1 is down, 1 is up. We normalize arbitrary amount.
    lines = amount // 100 if amount != 0 else 0
    if lines == 0 and amount != 0:
        lines = 1 if amount > 0 else -1
        
    scroll_event = Quartz.CGEventCreateScrollWheelEvent(
        None,
        Quartz.kCGScrollEventUnitLine,
        1, # number of wheels
        lines
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, scroll_event)
    print(f"滚动鼠标：{lines} lines")


if __name__ == "__main__":
    pass

