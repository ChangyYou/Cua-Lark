"""
Grid helpers shared by platform-specific interaction modules.
"""


def grid_to_absolute_coordinates(
    grid_number: int,
    grid_info: dict,
    offset_ratio: float = 0.5,
) -> tuple[int, int]:
    """
    Convert a grid number to an absolute screen coordinate.

    Args:
        grid_number: Grid cell number, starting from 1.
        grid_info: Metadata returned by the screen capture module.
        offset_ratio: Vertical offset inside the cell. ``0.5`` is center,
            ``0.8`` is near the bottom edge.
    """
    columns = grid_info["grid_size"]
    row = (grid_number - 1) // columns
    col = (grid_number - 1) % columns

    x = int(col * grid_info["cell_width"] + grid_info["cell_width"] / 2)
    y = int((row + offset_ratio) * grid_info["cell_height"])

    window_info = grid_info.get("window_info")
    if window_info:
        x += window_info["left"]
        y += window_info["top"]

    return x, y

