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


def add_grid_overlay(
    image: Image.Image,
    grid_size: int,
    font_candidates: list[str],
) -> Image.Image:
    """Draw a red grid with numeric labels on top of the image."""
    result = image.copy()
    draw = ImageDraw.Draw(result)

    width, height = image.size
    cell_width = width / grid_size
    cell_height = height / grid_size
    font_size = int(min(cell_width, cell_height) * 0.15)
    font = load_font(font_candidates, font_size)

    number = 1
    for row in range(grid_size):
        for col in range(grid_size):
            x1 = col * cell_width
            y1 = row * cell_height
            x2 = x1 + cell_width
            y2 = y1 + cell_height

            draw.rectangle([x1, y1, x2, y2], outline="red", width=1)

            text = str(number)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = x1 + (cell_width - text_width) / 2
            text_y = y1 + (cell_height - text_height) / 2
            draw.text((text_x, text_y), text, fill="red", font=font)

            number += 1

    return result


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

