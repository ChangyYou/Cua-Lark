"""
macOS platform implementation exports.
"""

from platforms.macos.click import click_at, scroll
from platforms.macos.hotkey import open_search, press, send_message
from platforms.macos.keyboard import input_message, paste_text, type_english
from platforms.macos.screen import ScreenCapture, capture_lark_window

__all__ = [
    "ScreenCapture",
    "capture_lark_window",
    "click_at",
    "scroll",
    "input_message",
    "open_search",
    "paste_text",
    "press",
    "send_message",
    "type_english",
]

