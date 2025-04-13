"""Image utility for adding measurement rulers to screenshots.

This module provides a function to add horizontal and vertical rulers to an image,
useful for visual measurement and debugging in screenshot workflows.
"""

import sys
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont

@dataclass
class RulerSettings: # pylint: disable=too-many-instance-attributes
    """Configuration for ruler appearance."""
    size: int = 30
    major_interval: int = 100
    mid_interval: int = 50
    minor_interval: int = 10
    major_length: int = 8
    mid_length: int = 6
    minor_length: int = 3
    color: str = "#555"
    bg_color: str = "#f0f0f0"
@dataclass
class TickInfo:
    """Information needed to draw a single tick."""
    pos: int
    length: int
    text: str = ""

def add_rulers(input_path: str, output_path: str = None) -> str:
    """Adds horizontal and vertical measurement rulers to an image.

    Args:
        input_path: Path to the input image.
        output_path: Path to save the output image. Defaults to input_path.

    Returns:
        The path to the saved output image.
    """
    settings = RulerSettings()
    output_path = output_path or input_path

    try:
        with Image.open(input_path) as orig_img:
            img = _create_base_image(orig_img, settings)
            draw = ImageDraw.Draw(img)
            fonts = _load_fonts()

            _draw_horizontal_ruler(orig_img.width, draw, fonts, settings)
            _draw_vertical_ruler(orig_img.height, draw, fonts, settings)

            img.save(output_path)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}")
        sys.exit(1)
    except IOError as e:
        print(f"Error processing image: {e}")
        sys.exit(1)

    return output_path

def _create_base_image(orig_img: Image.Image, settings: RulerSettings) -> Image.Image:
    """Creates a new image canvas with space for rulers and pastes the original."""
    new_width = orig_img.width + settings.size
    new_height = orig_img.height + settings.size
    img = Image.new("RGB", (new_width, new_height), settings.bg_color)
    img.paste(orig_img, (settings.size, settings.size))
    return img

def _load_fonts() -> tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    """Loads preferred fonts or falls back to default."""
    try:
        major_font = ImageFont.truetype("DejaVuSans.ttf", 10)
        mid_font = ImageFont.truetype("DejaVuSans.ttf", 8)
    except IOError:
        major_font = ImageFont.load_default()
        mid_font = major_font
    return major_font, mid_font

def _draw_horizontal_ruler(width: int, draw: ImageDraw.Draw,
                         fonts: tuple, settings: RulerSettings) -> None:
    """Draws the horizontal ruler with ticks and labels."""
    major_font, mid_font = fonts
    for x in range(0, width, settings.minor_interval):
        is_major = x % settings.major_interval == 0
        is_mid = x % settings.mid_interval == 0

        if is_major:
            tick_info = TickInfo(pos=x, length=settings.major_length, text=str(x))
            _draw_tick(draw, tick_info, major_font, settings, horizontal=True)
        elif is_mid:
            tick_info = TickInfo(pos=x, length=settings.mid_length, text=str(x))
            _draw_tick(draw, tick_info, mid_font, settings, horizontal=True)
        else:
            _draw_minor_tick(draw, x, settings.minor_length, settings, True)

def _draw_vertical_ruler(height: int, draw: ImageDraw.Draw,
                       fonts: tuple, settings: RulerSettings) -> None:
    """Draws the vertical ruler with ticks and labels."""
    major_font, mid_font = fonts
    for y in range(0, height, settings.minor_interval):
        is_major = y % settings.major_interval == 0
        is_mid = y % settings.mid_interval == 0

        if is_major:
            tick_info = TickInfo(pos=y, length=settings.major_length, text=str(y))
            _draw_tick(draw, tick_info, major_font, settings, horizontal=False)
        elif is_mid:
            tick_info = TickInfo(pos=y, length=settings.mid_length, text=str(y))
            _draw_tick(draw, tick_info, mid_font, settings, horizontal=False)
        else:
            _draw_minor_tick(draw, y, settings.minor_length, settings, False)

def _draw_tick(draw: ImageDraw.Draw, tick_info: TickInfo, font: ImageFont.FreeTypeFont,
             settings: RulerSettings, *, horizontal: bool) -> None:
    """Draws a major or mid tick mark with its label."""
    if horizontal:
        x = tick_info.pos + settings.size
        draw.line(
            (x, settings.size - tick_info.length, x, settings.size),
            fill=settings.color,
            width=1
        )
        text_width = font.getlength(tick_info.text)
        draw.text(
            (
                x - text_width / 2,
                settings.size - tick_info.length - font.size - 2
            ),
            tick_info.text, fill=settings.color, font=font
        )
    else:
        y = tick_info.pos + settings.size
        draw.line(
            (settings.size - tick_info.length, y, settings.size, y),
            fill=settings.color,
            width=1
        )
        text_width = font.getlength(tick_info.text)
        text_x = max(
            2, settings.size - tick_info.length - text_width - 2
        )
        draw.text((text_x, y - font.size // 2), tick_info.text, fill=settings.color, font=font)

def _draw_minor_tick(draw: ImageDraw.Draw, pos: int, length: int, settings: RulerSettings,
                   horizontal: bool) -> None:
    """Draws a minor tick mark."""
    if horizontal:
        x = pos + settings.size
        draw.line((x, settings.size - length, x, settings.size), fill=settings.color, width=1)
    else:
        y = pos + settings.size
        draw.line((settings.size - length, y, settings.size, y), fill=settings.color, width=1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        add_rulers(sys.argv[1])
    else:
        print("Usage: python add_rulers.py <input_image_path> [output_image_path]")
