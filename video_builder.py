"""
Assembles scenes (text + matching AI-generated image) into a finished MP4.
Captions render word-by-word, synced to real spoken timestamps — but as ONE
dynamic clip (a make_frame callback that looks up the currently-active word
at render time), not hundreds of separate overlapping clips. The earlier
one-clip-per-word approach caused a severe render slowdown (compositing
hundreds of overlapping clips is expensive) and led to workflow timeouts on
longer scripts — this fixes that while keeping the same word-by-word look.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    AudioFileClip, ImageClip, VideoClip, CompositeVideoClip,
    concatenate_videoclips, vfx,
)

import config

FPS = 24
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
CROSSFADE_DURATION = 0.35
TRAILING_BUFFER = 0.3

ORIENTATIONS = {
    "landscape": {"w": 1920, "h": 1080},
    "vertical": {"w": 1080, "h": 1920},
}


def _load_pil_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _cover_scale(clip, target_w, target_h):
    img_w, img_h = clip.size
    return max(target_w / img_w, target_h / img_h)


def _ken_burns_clip(img_path: Path, duration: float, w: int, h: int, zoom_direction: int):
    clip = ImageClip(str(img_path)).set_duration(duration)
    base_scale = _cover_scale(clip, w, h) * 1.12
    zoom_ratio = 0.09

    if zoom_direction >= 0:
        scale_fn = lambda t: base_scale * (1 + zoom_ratio * (t / duration))
    else:
        scale_fn = lambda t: base_scale * (1 + zoom_ratio) * (1 - zoom_ratio * 0.6 * (t / duration))

    clip = clip.fx(vfx.resize, scale_fn)
    clip = clip.set_position("center")
    return clip


def _find_active_word(words: list[dict], t: float) -> str:
    """words must be sorted by start time. Binary search for the word whose
    [start, extended_end) window contains t."""
    if not words:
        return ""
    lo, hi = 0, len(words) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if words[mid]["start"] <= t:
            lo = mid
        else:
            hi = mid - 1
    w = words[lo]
    if w["start"] <= t <= w["display_end"]:
        return w["word"]
    return ""


def _build_caption_layer(all_words: list[dict], duration: float, w: int, h: int,
                          fontsize: int, bottom_margin: int):
    """One dynamic clip for ALL word captions in the video, instead of one
    clip per word — this is what keeps render time reasonable regardless of
    how many words the script has. Each unique word is only rendered with
    PIL once and cached, since the same word typically stays on screen for
    several consecutive frames."""
    font = _load_pil_font(fontsize)
    color_cache: dict[str, np.ndarray] = {}
    mask_cache: dict[str, np.ndarray] = {}
    blank_color = np.zeros((h, w, 3), dtype=np.uint8)
    blank_mask = np.zeros((h, w), dtype=np.float64)

    def _render_word(word: str, as_mask: bool):
        mode = "L" if as_mask else "RGBA"
        fill_val = 0 if as_mask else (0, 0, 0, 0)
        img = Image.new(mode, (w, h), fill_val)
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), word, font=font)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        y = h - bottom_margin
        if as_mask:
            draw.text((x, y), word, font=font, fill=255, stroke_width=6, stroke_fill=255)
            return np.array(img) / 255.0
        else:
            draw.text((x, y), word, font=font, fill=(255, 255, 255, 255),
                       stroke_width=6, stroke_fill=(0, 0, 0, 255))
            return np.array(img.convert("RGB"))

    def make_frame(t):
        word = _find_active_word(all_words, t)
        if not word:
            return blank_color
        if word not in color_cache:
            color_cache[word] = _render_word(word, as_mask=False)
        return color_cache[word]

    def make_mask_frame(t):
        word = _find_active_word(all_words, t)
        if not word:
            return blank_mask
        if word not in mask_cache:
            mask_cache[word] = _render_word(word, as_mask=True)
        return mask_cache[word]

    clip = VideoClip(make_frame, duration=duration)
    mask_clip = VideoClip(make_mask_frame, duration=duration, ismask=True)
    clip = clip.set_mask(mask_clip)
    return clip


def build_video_from_scenes(scenes: list[dict], audio_path: Path, output_path: Path,
                             orientation: str = "landscape") -> Path:
    dims = ORIENTATIONS[orientation]
    w, h = dims["w"], dims["h"]
    fontsize = 64 if orientation == "vertical" else 66
    bottom_margin = 420 if orientation == "vertical" else 220

    audio = AudioFileClip(str(audio_path))

    bg_clips = []
    for i, scene in enumerate(scenes):
        dur = scene["duration"]
        zoom_dir = 1 if i % 2 == 0 else -1
        clip = _ken_burns_clip(scene["image"], dur, w, h, zoom_dir)
        if i > 0:
            clip = clip.crossfadein(CROSSFADE_DURATION)
        bg_clips.append(clip)

    background = concatenate_videoclips(bg_clips, method="compose", padding=-CROSSFADE_DURATION)
    background = background.set_audio(audio).set_duration(audio.duration)

    all_words = []
    for scene in scenes:
        all_words.extend(scene.get("words", []))

    for i, wd in enumerate(all_words):
        if i + 1 < len(all_words):
            wd["display_end"] = all_words[i + 1]["start"]
        else:
            wd["display_end"] = wd["end"] + TRAILING_BUFFER

    caption_layer = _build_caption_layer(all_words, audio.duration, w, h, fontsize, bottom_margin)

    final = CompositeVideoClip([background, caption_layer], size=(w, h))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(
        str(output_path), fps=FPS, codec="libx264", audio_codec="aac",
        preset="veryfast", threads=2,
    )
    return output_path


if __name__ == "__main__":
    print("Run this via main.py — needs scenes with matching images + words + an audio file.")
