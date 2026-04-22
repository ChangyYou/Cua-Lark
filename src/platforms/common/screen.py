"""
Shared image helpers for platform-specific screen capture modules.
"""

from PIL import Image, ImageDraw, ImageFont


def load_font(font_candidates: list[str], font_size: int):
    """Load the first available font from the candidate list."""
    for font_path in font_candidates:
        try:
            return ImageFont.truetype(font_path, font_size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_grid_info(grid_size: int, image: Image.Image, window_info: dict | None) -> dict:
    """Build the shared grid metadata structure."""
    width, height = image.size
    return {
        "grid_size": grid_size,
        "cell_width": width / grid_size,
        "cell_height": height / grid_size,
        "image_width": width,
        "image_height": height,
        "window_info": window_info,
    }

