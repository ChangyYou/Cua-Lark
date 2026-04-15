"""
执行层 - 鼠标点击模块

根据网格编号执行点击操作。
"""

import pyautogui
import time

from src.perception.screen import ScreenCapture


def click_grid(grid_number: int, grid_info: dict) -> None:
    """
    点击指定网格编号的位置

    Args:
        grid_number: 网格编号（从1开始）
        grid_info: 网格信息字典（来自 ScreenCapture）
    """
    rows = grid_info["grid_size"]
    cols = grid_info["grid_size"]

    # 计算行列索引（从0开始）
    row = (grid_number - 1) // cols
    col = (grid_number - 1) % cols

    # 计算格子中心点
    x = int(col * grid_info["cell_width"] + grid_info["cell_width"] / 2)
    y = int(row * grid_info["cell_height"] + grid_info["cell_height"] / 2)

    # 加上窗口偏移，得到绝对屏幕坐标
    if grid_info["window_info"]:
        x += grid_info["window_info"]["left"]
        y += grid_info["window_info"]["top"]

    # 执行点击
    pyautogui.click(x, y)
    print(f"点击坐标: ({x}, {y})")


def click_and_wait(grid_number: int, grid_info: dict, wait: float = 1.0) -> None:
    """点击后等待"""
    click_grid(grid_number, grid_info)
    time.sleep(wait)


def click_grid_bottom(grid_number: int, grid_info: dict, offset_ratio: float = 0.8) -> None:
    """
    点击指定网格编号的下边界位置

    Args:
        grid_number: 网格编号（从1开始）
        grid_info: 网格信息字典
        offset_ratio: 下边界偏移比例（0.5=中间, 0.8=下半部分, 1.0=最底部）
    """
    rows = grid_info["grid_size"]
    cols = grid_info["grid_size"]

    # 计算行列索引（从0开始）
    row = (grid_number - 1) // cols
    col = (grid_number - 1) % cols

    # 计算格子下边界位置
    x = int(col * grid_info["cell_width"] + grid_info["cell_width"] / 2)
    y = int((row + offset_ratio) * grid_info["cell_height"])

    # 加上窗口偏移，得到绝对屏幕坐标
    if grid_info["window_info"]:
        x += grid_info["window_info"]["left"]
        y += grid_info["window_info"]["top"]

    # 执行点击
    pyautogui.click(x, y)
    print(f"点击坐标(下边界): ({x}, {y})")


if __name__ == "__main__":
    # 测试：先截取，然后点击指定网格
    print("截取飞书窗口...")
    capture = ScreenCapture(grid_size=6)
    img, grid_info = capture.capture_with_grid()
    img.save("captures/test_click.png")

    print(f"截图尺寸: {grid_info['image_width']}x{grid_info['image_height']}")
    print(f"窗口位置: left={grid_info['window_info']['left']}, top={grid_info['window_info']['top']}")
    print(f"网格大小: {grid_info['grid_size']}x{grid_info['grid_size']}")
    print(f"单元格尺寸: {grid_info['cell_width']:.1f}x{grid_info['cell_height']:.1f}")

    # 等待2秒让用户准备
    print("2秒后开始点击网格23...")
    time.sleep(2)

    click_grid(23, grid_info)
