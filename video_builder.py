"""
Step 5: Assemble images + voiceover + captions into a finished MP4.
Supports two orientations:
  - "landscape" (1920x1080) — for the main YouTube page / regular video tab
  - "vertical"  (1080x1920) — for YouTube Shorts (also needs a #Shorts tag
    in the title/description, handled in main.py)
"""
import textwrap
from pathlib import Path

from moviepy.editor import (
    AudioFileClip, ImageClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, vfx,
)

import config

FPS = 24
FONT = "DejaVu-Sans-Bold"

ORIENTATIONS = {
    "landscape": {"w": 1920, "h": 1080},
    "vertical": {"w": 1080, "h": 1920},
}


def _cover_scale(clip, target_w, target_h):
    img_w, img_h = clip.size
    return max(target_w / img_w, target_h / img_h)


def _ken_burns_clip(img_path: Path, duration: float, w: int, h: int, zoom_ratio: float = 0.07):
    clip = ImageClip(str(img_path)).set_duration(duration)
    base_scale = _cover_scale(clip, w, h) * 1.1
    clip = clip.fx(vfx.resize, lambda t: base_scale * (1 + zoom_ratio * (t / duration)))
    clip = clip.set_position("center")
    return clip


def _wrapped_caption(text: str, duration: float, start: float, w: int, h: int, wrap_width: int):
    wrapped = "\n".join(textwrap.wrap(text, width=wrap_width))
    txt = TextClip(
        wrapped, fontsize=42 if w < h else 46, color="white", font=FONT,
        stroke_color="black", stroke_width=3,
        method="caption", size=(w - 120, None), align="center",
        bg_color="rgba(0,0,0,0.6)",
    )
    bottom_margin = 500 if w < h else 280   # vertical needs more room above the safe zone
    txt = txt.set_position(("center", h - bottom_margin)).set_start(start).set_duration(duration)
    return txt


def build_video(images: list[Path], audio_path: Path, script_text: str,
                 headline: str, output_path: Path, orientation: str = "landscape") -> Path:
    dims = ORIENTATIONS[orientation]
    w, h = dims["w"], dims["h"]
    wrap_width = 26 if orientation == "vertical" else 36

    audio = AudioFileClip(str(audio_path))
    duration = audio.duration

    if not images:
        raise ValueError("No images provided for video assembly")

    per_image = duration / len(images)
    bg_clips = [_ken_burns_clip(p, per_image, w, h) for p in images]
    background = concatenate_videoclips(bg_clips, method="compose").set_audio(audio)

    headline_top = 200 if orientation == "vertical" else None  # None -> "center" full-frame center
    headline_txt = TextClip(
        headline, fontsize=52 if orientation == "vertical" else 60, color="white", font=FONT,
        stroke_color="black", stroke_width=4,
        method="caption", size=(w - 160, None), align="center",
        bg_color="rgba(0,0,0,0.55)",
    )
    pos = ("center", headline_top) if headline_top else "center"
    headline_txt = headline_txt.set_position(pos).set_start(0).set_duration(min(5, duration))

    sentences = [s.strip() for s in script_text.replace("\n", " ").split(". ") if s.strip()]
    chunks = []
    chunk_size = max(1, len(sentences) // 7)
    for i in range(0, len(sentences), chunk_size):
        chunks.append(". ".join(sentences[i:i + chunk_size]))

    caption_clips = []
    if chunks:
        seg = duration / len(chunks)
        for i, chunk in enumerate(chunks):
            caption_clips.append(_wrapped_caption(chunk, seg, i * seg, w, h, wrap_width))

    brand = TextClip(
        "NIGERIA NEWS TODAY", fontsize=30, color="white", font=FONT,
        stroke_color="black", stroke_width=2,
        bg_color="rgba(0,0,0,0.4)",
    ).set_position((30, 60 if orientation == "vertical" else 30)).set_duration(duration)

    final = CompositeVideoClip(
        [background, headline_txt, brand, *caption_clips], size=(w, h)
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(
        str(output_path), fps=FPS, codec="libx264", audio_codec="aac",
        preset="medium", threads=4,
    )
    return output_path


if __name__ == "__main__":
    print("Run this via main.py — it needs images + an audio file + a script to work with.")
