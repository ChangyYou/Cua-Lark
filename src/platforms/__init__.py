"""
Platform adapter layer.

This module exposes a stable cross-platform interface while delegating the
actual implementation to the current operating system package.
"""

import platform


def get_platform() -> str:
    """Return the normalized current platform name."""
    system_name = platform.system()
    if system_name == "Windows":
        return "windows"
    if system_name == "Darwin":
        return "macos"
    if system_name == "Linux":
        return "linux"
    return "unknown"


CURRENT_PLATFORM = get_platform()

if CURRENT_PLATFORM == "windows":
    from platforms.windows import (
        ScreenCapture,
        capture_lark_window,
        click_at,
        click_grid,
        click_grid_bottom,
        input_message,
        open_search,
        paste_text,
        press,
        send_message,
        type_english,
    )
elif CURRENT_PLATFORM == "macos":
    from platforms.macos import (
        ScreenCapture,
        capture_lark_window,
        click_at,
        click_grid,
        click_grid_bottom,
        input_message,
        open_search,
        paste_text,
        press,
        send_message,
        type_english,
    )
else:
    raise ImportError(f"不支持的操作系统：{CURRENT_PLATFORM}")


__all__ = [
    "CURRENT_PLATFORM",
    "ScreenCapture",
    "capture_lark_window",
    "click_at",
    "click_grid",
    "click_grid_bottom",
    "input_message",
    "open_search",
    "paste_text",
    "press",
    "send_message",
    "type_english",
]

