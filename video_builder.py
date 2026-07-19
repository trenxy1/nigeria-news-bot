"""
Assembles scenes (text + matching AI-generated image) into a finished MP4.
Includes crossfade transitions between scenes and alternating zoom-in/zoom-out
motion, so fast-changing AI images read as smooth/produced rather than a
choppy slideshow. Works with any scene list (each scene just needs "text",
"duration", and "image") regardless of how those scenes were chunked upstream.
"""
import textwrap
from pathlib import Path

from moviepy.editor import (
    AudioFileClip, ImageClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, vfx,
)

import config

FPS = 24
FONT = "DejaVu-Sans-Bold-Oblique"
FONT_FALLBACK = "DejaVu-Sans-Bold"
CROSSFADE_DURATION = 0.35   # seconds — subtle, smooths cuts without feeling slow

ORIENTATIONS = {
    "landscape": {"w": 1920, "h": 1080},
    "vertical": {"w": 1080, "h": 1920},
}


def _cover_scale(clip, target_w, target_h):
    img_w, img_h = clip.size
    return max(target_w / img_w, target_h / img_h)


def _ken_burns_clip(img_path: Path, duration: float, w: int, h: int, zoom_direction: int):
    """zoom_direction: 1 = zoom in, -1 = zoom out. Alternating this across
    scenes reads as more dynamic/intentional than every clip zooming the
    same way."""
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


def _make_text_clip(text: str, fontsize: int, w: int, wrap_width: int, stroke_width: int):
    wrapped = "\n".join(textwrap.wrap(text, width=wrap_width))
    try:
        return TextClip(
            wrapped, fontsize=fontsize, color="white", font=FONT,
            stroke_color="black", stroke_width=stroke_width,
            method="caption", size=(w - 100, None), align="center",
        )
    except Exception:
        return TextClip(
            wrapped, fontsize=fontsize, color="white", font=FONT_FALLBACK,
            stroke_color="black", stroke_width=stroke_width,
            method="caption", size=(w - 100, None), align="center",
        )


def build_video_from_scenes(scenes: list[dict], audio_path: Path, output_path: Path,
                             orientation: str = "landscape") -> Path:
    dims = ORIENTATIONS[orientation]
    w, h = dims["w"], dims["h"]
    wrap_width = 22 if orientation == "vertical" else 32
    fontsize = 54 if orientation == "vertical" else 58

    audio = AudioFileClip(str(audio_path))

    bg_clips = []
    caption_clips = []
    t_cursor = 0.0

    for i, scene in enumerate(scenes):
        dur = scene["duration"]
        zoom_dir = 1 if i % 2 == 0 else -1

        clip = _ken_burns_clip(scene["image"], dur, w, h, zoom_dir)
        if i > 0:
            clip = clip.crossfadein(CROSSFADE_DURATION)
        bg_clips.append(clip)

        cap = _make_text_clip(scene["text"], fontsize, w, wrap_width, stroke_width=3)
        bottom_margin = 420 if orientation == "vertical" else 220
        cap = cap.set_position(("center", h - bottom_margin)).set_start(t_cursor).set_duration(dur)
        caption_clips.append(cap)

        t_cursor += dur

    background = concatenate_videoclips(bg_clips, method="compose", padding=-CROSSFADE_DURATION)
    background = background.set_audio(audio).set_duration(audio.duration)

    final = CompositeVideoClip([background, *caption_clips], size=(w, h))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(
        str(output_path), fps=FPS, codec="libx264", audio_codec="aac",
        preset="medium", threads=4,
    )
    return output_path


if __name__ == "__main__":
    print("Run this via main.py — needs scenes with matching images + an audio file.")
  
