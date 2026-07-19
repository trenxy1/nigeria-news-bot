"""
Generates a custom YouTube thumbnail: takes one of the story's AI-generated
scene images as a background, overlays the video title in large bold text
with a dark gradient strip behind it for readability. Custom thumbnails
consistently outperform YouTube's auto-picked video frame for click-through.

YouTube requires 1280x720 for thumbnails (16:9), under 2MB, jpg/png.
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


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def generate_thumbnail(background_image_path: Path, title: str, output_path: Path) -> Path:
    img = Image.open(background_image_path).convert("RGB")

    # cover-crop to 1280x720
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

    # darken the lower third so white text stays readable over any image
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    strip_top = int(THUMB_H * 0.58)
    draw_overlay.rectangle([(0, strip_top), (THUMB_W, THUMB_H)], fill=(0, 0, 0, 165))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)
    font = _load_font(72)

    wrapped = textwrap.fill(title.upper(), width=22)
    lines = wrapped.split("\n")[:3]  # cap at 3 lines so it doesn't overflow

    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])
    total_text_h = sum(line_heights) + (len(lines) - 1) * 12

    y = THUMB_H - 40 - total_text_h
    for line, lh in zip(lines, line_heights):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (THUMB_W - line_w) // 2
        # stroke/outline for legibility over any background
        draw.text((x, y), line, font=font, fill="white",
                   stroke_width=4, stroke_fill="black")
        y += lh + 12

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "JPEG", quality=90)
    return output_path


if __name__ == "__main__":
    print("Run this via main.py — needs a background image and a title.")
