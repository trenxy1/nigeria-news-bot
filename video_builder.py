"""
Step 5: Assemble images + voiceover + captions into a finished 1080p MP4.

Uses DejaVu Sans Bold, which is a real bold font pre-installed on the Linux
runner (Arial doesn't exist on Linux, which is why earlier captions looked
thin/unreadable even though we requested "Arial-Bold").
"""
import textwrap
from pathlib import Path

from moviepy.editor import (
    AudioFileClip, ImageClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, vfx,
)

import config

VIDEO_W, VIDEO_H = 1920, 1080
FPS = 24
FONT = "DejaVu-Sans-Bold"


def _ken_burns_clip(img_path: Path, duration: float, zoom_ratio: float = 0.06):
    clip = ImageClip(str(img_path)).set_duration(duration)
    clip = clip.resize(height=VIDEO_H + 100)
    clip = clip.fx(vfx.resize, lambda t: 1 + zoom_ratio * (t / duration))
    clip = clip.set_position("center")
    return clip


def _wrapped_caption(text: str, duration: float, start: float):
    wrapped = "\n".join(textwrap.wrap(text, width=36))
    txt = TextClip(
        wrapped, fontsize=46, color="white", font=FONT,
        stroke_color="black", stroke_width=3,
        method="caption", size=(VIDEO_W - 160, None), align="center",
        bg_color="rgba(0,0,0,0.6)",
    )
    txt = txt.set_position(("center", VIDEO_H - 280)).set_start(start).set_duration(duration)
    return txt


def build_video(images: list[Path], audio_path: Path, script_text: str,
                 headline: str, output_path: Path) -> Path:
    audio = AudioFileClip(str(audio_path))
    duration = audio.duration

    if not images:
        raise ValueError("No images provided for video assembly")

    per_image = duration / len(images)
    bg_clips = [_ken_burns_clip(p, per_image) for p in images]
    background = concatenate_videoclips(bg_clips, method="compose").set_audio(audio)

    headline_txt = TextClip(
        headline, fontsize=60, color="white", font=FONT,
        stroke_color="black", stroke_width=4,
        method="caption", size=(VIDEO_W - 260, None), align="center",
        bg_color="rgba(0,0,0,0.55)",
    )
    headline_txt = headline_txt.set_position("center").set_start(0).set_duration(min(5, duration))

    sentences = [s.strip() for s in script_text.replace("\n", " ").split(". ") if s.strip()]
    chunks = []
    chunk_size = max(1, len(sentences) // 7)
    for i in range(0, len(sentences), chunk_size):
        chunks.append(". ".join(sentences[i:i + chunk_size]))

    caption_clips = []
    if chunks:
        seg = duration / len(chunks)
        for i, chunk in enumerate(chunks):
            caption_clips.append(_wrapped_caption(chunk, seg, start=i * seg))

    brand = TextClip(
        "NIGERIA NEWS TODAY", fontsize=32, color="white", font=FONT,
        stroke_color="black", stroke_width=2,
        bg_color="rgba(0,0,0,0.4)",
    ).set_position((30, 30)).set_duration(duration)

    final = CompositeVideoClip(
        [background, headline_txt, brand, *caption_clips], size=(VIDEO_W, VIDEO_H)
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(
        str(output_path), fps=FPS, codec="libx264", audio_codec="aac",
        preset="medium", threads=4,
    )
    return output_path


if __name__ == "__main__":
    print("Run this via main.py — it needs images + an audio file + a script to work with.")
