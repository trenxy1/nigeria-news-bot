"""
Step 5: Assemble images + voiceover + captions into a finished 1080p MP4.

NOTE (Windows): TextClip requires ImageMagick to be installed and on PATH.
Download from https://imagemagick.org/script/download.php#windows
During install, check "Install legacy utilities" and "Add to system PATH".
If MoviePy still can't find it, set IMAGEMAGICK_BINARY below to the exe path,
e.g. r"C:\\Program Files\\ImageMagick-7.1.1-Q16\\magick.exe"
"""
import textwrap
from pathlib import Path

from moviepy.editor import (
    AudioFileClip, ImageClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, vfx,
)

import config

# Uncomment and edit on Windows if MoviePy can't auto-find ImageMagick:
# from moviepy.config import change_settings
# change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe"})

VIDEO_W, VIDEO_H = 1920, 1080
FPS = 24


def _ken_burns_clip(img_path: Path, duration: float, zoom_ratio: float = 0.06):
    """Slow zoom-in on a still image so it doesn't look like a static slideshow."""
    clip = ImageClip(str(img_path)).set_duration(duration)
    clip = clip.resize(height=VIDEO_H + 100)  # oversize slightly so zoom has room
    clip = clip.fx(vfx.resize, lambda t: 1 + zoom_ratio * (t / duration))
    clip = clip.set_position("center")
    return clip


def _wrapped_caption(text: str, duration: float, start: float):
    wrapped = "\n".join(textwrap.wrap(text, width=42))
    txt = TextClip(
        wrapped, fontsize=34, color="white", font="Arial-Bold",
        stroke_color="black", stroke_width=1.5,
        method="caption", size=(VIDEO_W - 200, None), align="center",
    )
    txt = txt.set_position(("center", VIDEO_H - 220)).set_start(start).set_duration(duration)
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

    # Headline card for first 5 seconds
    headline_txt = TextClip(
        headline, fontsize=54, color="white", font="Arial-Bold",
        stroke_color="black", stroke_width=2,
        method="caption", size=(VIDEO_W - 300, None), align="center",
    )
    headline_txt = headline_txt.set_position("center").set_start(0).set_duration(min(5, duration))

    # Break the script into ~3 caption chunks spread across the runtime
    sentences = [s.strip() for s in script_text.replace("\n", " ").split(". ") if s.strip()]
    chunks = []
    chunk_size = max(1, len(sentences) // 4)
    for i in range(0, len(sentences), chunk_size):
        chunks.append(". ".join(sentences[i:i + chunk_size]))

    caption_clips = []
    if chunks:
        seg = duration / len(chunks)
        for i, chunk in enumerate(chunks):
            caption_clips.append(_wrapped_caption(chunk, seg, start=i * seg))

    # "NIGERIA NEWS TODAY" title card overlay, top-left, persistent watermark-style
    brand = TextClip(
        "NIGERIA NEWS TODAY", fontsize=28, color="white", font="Arial-Bold",
        stroke_color="black", stroke_width=1,
    ).set_position((40, 40)).set_duration(duration)

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
                   
