"""
Assembles scenes (text + matching AI-generated image) into a finished MP4.
Captions now render WORD-BY-WORD, synced to each word's real spoken
timestamp (from scene["words"]) — text appears exactly as it's spoken,
instead of showing a whole sentence on screen all at once.
Includes crossfade transitions between background images and alternating
zoom-in/zoom-out motion.
"""
from pathlib import Path

from moviepy.editor import (
    AudioFileClip, ImageClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, vfx,
)

import config

FPS = 24
FONT = "DejaVu-Sans-Bold-Oblique"
FONT_FALLBACK = "DejaVu-Sans-Bold"
CROSSFADE_DURATION = 0.35
TRAILING_BUFFER = 0.3

ORIENTATIONS = {
    "landscape": {"w": 1920, "h": 1080},
    "vertical": {"w": 1080, "h": 1920},
}


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


def _make_word_clip(word: str, fontsize: int, w: int, stroke_width: int):
    try:
        return TextClip(
            word, fontsize=fontsize, color="white", font=FONT,
            stroke_color="black", stroke_width=stroke_width,
            method="caption", size=(w - 80, None), align="center",
        )
    except Exception:
        return TextClip(
            word, fontsize=fontsize, color="white", font=FONT_FALLBACK,
            stroke_color="black", stroke_width=stroke_width,
            method="caption", size=(w - 80, None), align="center",
        )


def build_video_from_scenes(scenes: list[dict], audio_path: Path, output_path: Path,
                             orientation: str = "landscape") -> Path:
    dims = ORIENTATIONS[orientation]
    w, h = dims["w"], dims["h"]
    fontsize = 64 if orientation == "vertical" else 66

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

    caption_clips = []
    bottom_margin = 420 if orientation == "vertical" else 220

    for i, wdata in enumerate(all_words):
        start = wdata["start"]
        end = all_words[i + 1]["start"] if i + 1 < len(all_words) else wdata["end"] + TRAILING_BUFFER
        duration = max(end - start, 0.05)

        cap = _make_word_clip(wdata["word"], fontsize, w, stroke_width=4)
        cap = cap.set_position(("center", h - bottom_margin)).set_start(start).set_duration(duration)
        caption_clips.append(cap)

    final = CompositeVideoClip([background, *caption_clips], size=(w, h))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(
        str(output_path), fps=FPS, codec="libx264", audio_codec="aac",
        preset="veryfast", threads=2,
    )
    return output_path


if __name__ == "__main__":
    print("Run this via main.py — needs scenes with matching images + words + an audio file.")
