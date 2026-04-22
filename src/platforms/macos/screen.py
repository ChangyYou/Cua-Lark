"""
macOS screen capture implementation.
"""

import subprocess

import mss
from PIL import Image

from platforms.common.screen import build_grid_info


MACOS_FONT_CANDIDATES = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
]


def _pick_lark_pid() -> int | None:
    """Pick the most likely foreground Lark process PID."""
    try:
        result = subprocess.run(
            ["pgrep", "-ifl", "lark"],
            capture_output=True,
            text=True,
        )
    except Exception:
        return None

    if not result.stdout.strip():
        return None

    helper_tokens = ("helper", "updater", "renderer", "gpu", "agent", "service")
    candidates = []
    for line in result.stdout.strip().splitlines():
        parts = line.split(maxsplit=1)
        if not parts:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        cmd = parts[1].lower() if len(parts) > 1 else ""
        is_helper = any(token in cmd for token in helper_tokens)
        score = 0 if is_helper else 100
        if "lark.app" in cmd or "feishu.app" in cmd:
            score += 20
        candidates.append((score, pid))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][1]


class ScreenCapture:
    """Capture the active macOS screen region used by Lark."""

    def __init__(self, grid_size: int = 6):
        self.grid_size = grid_size
        self.sct = mss.mss()
        self.window_info = None
        self._lark_pid = None

    def _get_window_list(self) -> list:
        """Collect visible windows through AppleScript."""
        try:
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    """
                    tell application "System Events"
                        set window_list to {}
                        repeat with proc in (every process whose visible is true)
                            repeat with win in every window of proc
                                copy {name:proc's name, title:win's name} to end of window_list
                            end repeat
                        end repeat
                        return window_list
                    end tell
                    """,
                ],
                capture_output=True,
                text=True,
            )
            return eval(result.stdout) if result.stdout else []
        except Exception as exc:
            print(f"获取窗口列表失败：{exc}")
            return []

    def find_lark_window(self) -> dict | None:
        """Locate the Lark application window or fall back to the primary monitor."""
        try:
            self._lark_pid = _pick_lark_pid()
            if self._lark_pid:
                print(f"找到飞书进程 (PID: {self._lark_pid})")

            monitors = self.sct.monitors
            monitor = monitors[1] if len(monitors) > 1 else monitors[0]
            self.window_info = {
                "left": monitor["left"],
                "top": monitor["top"],
                "width": monitor["width"],
                "height": monitor["height"],
                "pid": self._lark_pid,
            }
            return self.window_info
        except Exception as exc:
            print(f"查找飞书窗口失败：{exc}")
            monitor = self.sct.monitors[1] if len(self.sct.monitors) > 1 else self.sct.monitors[0]
            self.window_info = {
                "left": monitor["left"],
                "top": monitor["top"],
                "width": monitor["width"],
                "height": monitor["height"],
            }
            return self.window_info

    def capture_window(self, window_rect: dict | None = None) -> Image.Image:
        """Capture the given window rect or the inferred Lark window."""
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
    print(f"截图尺寸：{grid_info['image_width']}x{grid_info['image_height']}")
    print(f"网格大小：{grid_info['grid_size']}x{grid_info['grid_size']}")
    print(f"单元格尺寸：{grid_info['cell_width']:.1f}x{grid_info['cell_height']:.1f}")
    os.makedirs("captures", exist_ok=True)
    image.save("captures/lark_capture_macos.png")
    print("截图已保存到 captures/lark_capture_macos.png")
