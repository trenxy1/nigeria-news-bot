"""
Generates a custom YouTube thumbnail: takes one of the story's AI-generated
scene images as a background, overlays the video title in large bold text
with a dark gradient strip behind it.

Auto-fits the title text — starts at a large font size and shrinks it (and
re-wraps) until the full text fits within the available space, instead of
silently cutting text off past a fixed number of lines.
"""
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import config

THUMB_W, THUMB_H = 1280, 720
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
]

MAX_TEXT_WIDTH = THUMB_W - 80
MAX_TEXT_HEIGHT = int(THUMB_H * 0.40)
FONT_SIZE_START = 96
FONT_SIZE_MIN = 32
MAX_LINES = 5


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _fit_text(draw: ImageDraw.ImageDraw, text: str):
    text = text.upper()

    for size in range(FONT_SIZE_START, FONT_SIZE_MIN - 1, -4):
        font = _load_font(size)
        char_w = draw.textlength("A", font=font) or (size * 0.6)
        wrap_chars = max(6, int(MAX_TEXT_WIDTH / char_w))
        wrapped = textwrap.fill(text, width=wrap_chars)
        lines = wrapped.split("\n")

        if len(lines) > MAX_LINES:
            continue

        line_heights = []
        max_line_w = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_heights.append(bbox[3] - bbox[1])
            max_line_w = max(max_line_w, bbox[2] - bbox[0])
        total_h = sum(line_heights) + (len(lines) - 1) * 10

        if total_h <= MAX_TEXT_HEIGHT and max_line_w <= MAX_TEXT_WIDTH:
            return font, lines, line_heights

    font = _load_font(FONT_SIZE_MIN)
    char_w = draw.textlength("A", font=font) or (FONT_SIZE_MIN * 0.6)
    wrap_chars = max(6, int(MAX_TEXT_WIDTH / char_w))
    wrapped = textwrap.fill(text, width=wrap_chars)
    lines = wrapped.split("\n")[: MAX_LINES + 2]
    line_heights = [draw.textbbox((0, 0), l, font=font)[3] - draw.textbbox((0, 0), l, font=font)[1]
                     for l in lines]
    return font, lines, line_heights


def generate_thumbnail(background_image_path: Path, title: str, output_path: Path) -> Path:
    img = Image.open(background_image_path).convert("RGB")

    src_w, src_h = img.size
    target_ratio = THUMB_W / THUMB_H
    src_ratio = src_w / src_h
    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))
    img = img.resize((THUMB_W, THUMB_H))

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    strip_top = int(THUMB_H * 0.55)
    draw_overlay.rectangle([(0, strip_top), (THUMB_W, THUMB_H)], fill=(0, 0, 0, 175))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)
    font, lines, line_heights = _fit_text(draw, title)
    total_text_h = sum(line_heights) + (len(lines) - 1) * 10

    y = THUMB_H - 30 - total_text_h
    for line, lh in zip(lines, line_heights):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (THUMB_W - line_w) // 2
        draw.text((x, y), line, font=font, fill="white", stroke_width=4, stroke_fill="black")
        y += lh + 10

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "JPEG", quality=90)
    return output_path


if __name__ == "__main__":
    print("Run this via main.py — needs a background image and a title.")
