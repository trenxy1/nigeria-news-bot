"""
Assembles scenes (text + matching AI-generated image) into a finished MP4.
Captions update every 2-3 words (grouped from real word-timing data), using
standard TextClip objects — NOT a dynamic/masked VideoClip. Two earlier
approaches were tried and both caused severe render slowdowns on GitHub's
runners: one clip per single word (too many overlapping clips to composite),
and one dynamic VideoClip for the whole video (MoviePy's masked-dynamic-clip
compositing path is much slower per frame than its built-in TextClip path,
regardless of clip count). This phrase-grouped TextClip approach avoids both
problems while still updating frequently enough to track speech closely.
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
CROSSFADE_DURATION = 0.35
TRAILING_BUFFER = 0.3
WORDS_PER_CAPTION = 3   # how many words update together — tune lower for
                         # tighter sync, higher for fewer/cheaper clips

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


def _group_words_into_phrases(all_words: list[dict], group_size: int) -> list[dict]:
    """Groups consecutive words into small phrase-captions. Each phrase's
    duration comes from real timestamps (first word's start to next
    phrase's start, so there's no gap)."""
    phrases = []
    for i in range(0, len(all_words), group_size):
        chunk = all_words[i:i + group_size]
        phrases.append({"text": " ".join(w["word"] for w in chunk), "start": chunk[0]["start"],
                         "end": chunk[-1]["end"]})

    for i, p in enumerate(phrases):
        if i + 1 < len(phrases):
            p["duration"] = max(phrases[i + 1]["start"] - p["start"], 0.1)
        else:
            p["duration"] = max((p["end"] - p["start"]) + TRAILING_BUFFER, 0.1)

    return phrases


def build_video_from_scenes(scenes: list[dict], audio_path: Path, output_path: Path,
                             orientation: str = "landscape") -> Path:
    dims = ORIENTATIONS[orientation]
    w, h = dims["w"], dims["h"]
    wrap_width = 20 if orientation == "vertical" else 30
    fontsize = 58 if orientation == "vertical" else 60
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

    phrases = _group_words_into_phrases(all_words, WORDS_PER_CAPTION)

    caption_clips = []
    for p in phrases:
        cap = _make_text_clip(p["text"], fontsize, w, wrap_width, stroke_width=4)
        cap = cap.set_position(("center", h - bottom_margin)).set_start(p["start"]).set_duration(p["duration"])
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
