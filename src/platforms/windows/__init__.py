"""
Windows platform implementation exports.
"""

from platforms.windows.click import click_at, scroll
from platforms.windows.hotkey import open_search, press, send_message
from platforms.windows.keyboard import input_message, paste_text, type_english
from platforms.windows.screen import ScreenCapture, capture_lark_window

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

