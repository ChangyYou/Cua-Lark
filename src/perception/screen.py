"""
感知层 - 屏幕截取模块

负责截取飞书窗口区域，并在截图上叠加 Set-of-Mark 网格编号。
"""

import win32gui
import mss
import numpy as np
from PIL import Image, ImageDraw, ImageFont


class ScreenCapture:
    """屏幕截取器"""

    def __init__(self, grid_size: int = 6):
        """
        初始化截取器

        Args:
            grid_size: 网格行列数，默认 6x6
        """
        self.grid_size = grid_size
        self.sct = mss.mss()
        self.window_info = None
        self._lark_hwnd = None

    def _enum_windows_callback(self, hwnd, window_list):
        """枚举窗口回调函数"""
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:  # 只添加有标题的窗口
                window_list.append((hwnd, title))

    def list_all_windows(self) -> list:
        """列出所有可见窗口（调试用）"""
        window_list = []
        win32gui.EnumWindows(self._enum_windows_callback, window_list)
        return window_list

    def find_lark_window(self) -> dict | None:
        """
        查找飞书窗口位置

        Returns:
            窗口信息字典，包含 left, top, width, height
        """
        window_list = []
        win32gui.EnumWindows(self._enum_windows_callback, window_list)

        # 查找飞书窗口（标题必须包含"飞书"）
        lark_windows = [(hwnd, title) for hwnd, title in window_list
                       if "飞书" in title]

        if not lark_windows:
            print("未找到飞书窗口！当前所有窗口：")
            for hwnd, title in window_list[:20]:  # 只显示前20个
                print(f"  - {title}")
            # 如果没找到飞书窗口，截取主显示器
            monitors = mss.mss().monitors
            if len(monitors) > 1:
                self.window_info = {
                    "left": monitors[1]["left"],
                    "top": monitors[1]["top"],
                    "width": monitors[1]["width"],
                    "height": monitors[1]["height"]
                }
            else:
                self.window_info = {
                    "left": 0,
                    "top": 0,
                    "width": monitors[0]["width"],
                    "height": monitors[0]["height"]
                }
            return self.window_info

        # 优先选择主窗口（通常第一个就是）
        self._lark_hwnd, title = lark_windows[0]
        print(f"找到飞书窗口: {title} (hwnd: {self._lark_hwnd})")

        # 获取窗口客户区坐标
        left, top, right, bottom = win32gui.GetClientRect(self._lark_hwnd)

        # 将客户区坐标转换为屏幕坐标
        client_left, client_top = win32gui.ClientToScreen(self._lark_hwnd, (left, top))
        client_right, client_bottom = win32gui.ClientToScreen(self._lark_hwnd, (right, bottom))

        width = client_right - client_left
        height = client_bottom - client_top

        self.window_info = {
            "left": client_left,
            "top": client_top,
            "width": width,
            "height": height,
            "title": title,
            "hwnd": self._lark_hwnd
        }

        return self.window_info

    def capture_window(self, window_rect: dict | None = None) -> Image.Image:
        """
        截取窗口区域

        Args:
            window_rect: 窗口矩形区域，包含 left, top, width, height
                        如果为 None，则截取整个屏幕

        Returns:
            PIL Image 对象
        """
        if window_rect is None:
            window_rect = self.find_lark_window()

        if window_rect is None:
            raise RuntimeError("无法找到飞书窗口")

        self.window_info = window_rect

        # 使用 mss 截取指定区域
        screenshot = self.sct.grab(window_rect)

        # 转换为 PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

        return img

    def add_grid_overlay(self, img: Image.Image) -> Image.Image:
        """
        在截图上叠加 Set-of-Mark 网格编号

        Args:
            img: 原始截图

        Returns:
            叠加网格后的图像
        """
        # 复制图像避免修改原图
        result = img.copy()
        draw = ImageDraw.Draw(result)

        width, height = img.size
        rows, cols = self.grid_size, self.grid_size

        cell_width = width / cols
        cell_height = height / rows

        # 尝试使用默认字体，否则使用内置字体
        try:
            font = ImageFont.truetype("arial.ttf", int(min(cell_width, cell_height) * 0.15))
        except:
            font = ImageFont.load_default()

        # 绘制网格线和编号
        number = 1
        for row in range(rows):
            for col in range(cols):
                x1 = col * cell_width
                y1 = row * cell_height
                x2 = x1 + cell_width
                y2 = y1 + cell_height

                # 绘制矩形边框（红色）
                draw.rectangle(
                    [x1, y1, x2, y2],
                    outline="red",
                    width=1
                )

                # 计算编号文本位置（居中）
                text = str(number)
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                text_x = x1 + (cell_width - text_width) / 2
                text_y = y1 + (cell_height - text_height) / 2

                # 绘制编号
                draw.text(
                    (text_x, text_y),
                    text,
                    fill="red",
                    font=font
                )

                number += 1

        return result

    def capture_with_grid(self, window_rect: dict | None = None) -> tuple[Image.Image, dict]:
        """
        截取窗口并叠加网格

        Args:
            window_rect: 窗口矩形区域

        Returns:
            (叠加网格的图像, 网格信息字典)
        """
        # 截取窗口
        img = self.capture_window(window_rect)

        # 叠加网格
        img_with_grid = self.add_grid_overlay(img)

        # 网格信息
        width, height = img.size
        grid_info = {
            "grid_size": self.grid_size,
            "cell_width": width / self.grid_size,
            "cell_height": height / self.grid_size,
            "image_width": width,
            "image_height": height,
            "window_info": self.window_info
        }

        return img_with_grid, grid_info

    def grid_to_coordinates(self, grid_number: int, grid_info: dict) -> tuple[int, int]:
        """
        将网格编号转换为像素坐标（格子中心点）

        Args:
            grid_number: 网格编号（从1开始）
            grid_info: 网格信息字典

        Returns:
            (x, y) 像素坐标
        """
        rows = grid_info["grid_size"]
        cols = grid_info["grid_size"]

        # 计算行列索引（从0开始）
        row = (grid_number - 1) // cols
        col = (grid_number - 1) % cols

        # 计算格子中心点
        x = int(col * grid_info["cell_width"] + grid_info["cell_width"] / 2)
        y = int(row * grid_info["cell_height"] + grid_info["cell_height"] / 2)

        # 加上窗口偏移
        if grid_info["window_info"]:
            x += grid_info["window_info"]["left"]
            y += grid_info["window_info"]["top"]

        return x, y


def capture_lark_window(grid_size: int = 6) -> tuple[Image.Image, dict]:
    """
    快捷函数：截取飞书窗口并叠加网格

    Args:
        grid_size: 网格大小

    Returns:
        (叠加网格的图像, 网格信息字典)
    """
    capture = ScreenCapture(grid_size=grid_size)
    window_rect = capture.find_lark_window()
    return capture.capture_with_grid(window_rect)


if __name__ == "__main__":
    # 测试截取功能
    print("截取飞书窗口...")
    img, grid_info = capture_lark_window()
    print(f"截图尺寸: {grid_info['image_width']}x{grid_info['image_height']}")
    print(f"网格大小: {grid_info['grid_size']}x{grid_info['grid_size']}")
    print(f"单元格尺寸: {grid_info['cell_width']:.1f}x{grid_info['cell_height']:.1f}")

    # 保存截图
    import os
    os.makedirs("captures", exist_ok=True)
    img.save("captures/lark_capture.png")
    print("截图已保存到 captures/lark_capture.png")
