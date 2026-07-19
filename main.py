"""
Orchestrator: fetches headlines, picks the top-priority unused one, writes a
script, generates a voiceover with real word-timing data, generates one
AI image per sentence-level scene (generic/symbolic imagery — see config.py
for why real people aren't depicted), builds both landscape and vertical
videos from the SAME image set (no need to generate images twice), builds a
custom thumbnail, and uploads everything.

Usage:
    py main.py --count 1              # process 1 headline, no upload
    py main.py --count 1 --upload     # process and upload to YouTube
"""
import argparse
import json
import sys
import traceback
from datetime import date

from moviepy.editor import AudioFileClip

import config
import rss_fetch
import script_generator
import tts_generator
import scene_builder
import image_generate
import video_builder
import thumbnail_generator


def mark_used(headline_id: str):
    with open(config.HEADLINES_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)
    for item in items:
        if item["id"] == headline_id:
            item["used"] = True
    with open(config.HEADLINES_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def process_one(headline: dict, do_upload: bool) -> list[str]:
    print(f"\n=== {headline['title']} ({headline['priority']}) ===")

    print("[1/6] Generating script...")
    script_text = script_generator.generate_script(headline)
    print(f"({len(script_text.split())} words)")

    print("[2/6] Generating voiceover + word timing...")
    audio_path, boundaries = tts_generator.generate_audio_with_timing(script_text, headline["id"])

    total_duration = AudioFileClip(str(audio_path)).duration
    scenes = scene_builder.build_scenes(boundaries, total_audio_duration=total_duration)
    print(f"  {len(scenes)} scenes ({total_duration:.0f}s total audio)")

    print("[3/6] Generating AI images (reused for both video formats)...")
    image_paths = image_generate.generate_images_for_scenes(
        [s["text"] for s in scenes], headline["id"], 1920, 1080,
    )
    scenes = scenes[: len(image_paths)]
    for scene, img_path in zip(scenes, image_paths):
        scene["image"] = img_path

    print("[4/6] Building landscape video...")
    date_str = date.today().isoformat()
    landscape_path = config.VIDEO_DIR / f"{date_str}_{headline['id']}_landscape.mp4"
    video_builder.build_video_from_scenes(scenes, audio_path, landscape_path, orientation="landscape")

    print("[5/6] Building vertical (Shorts) video...")
    vertical_path = config.VIDEO_DIR / f"{date_str}_{headline['id']}_vertical.mp4"
    video_builder.build_video_from_scenes(scenes, audio_path, vertical_path, orientation="vertical")

    print("[6/6] Building thumbnail...")
    thumb_path = config.THUMBNAIL_DIR / f"{headline['id']}_thumb.jpg"
    thumbnail_generator.generate_thumbnail(scenes[0]["image"], headline["title"], thumb_path)

    print(f"[OK] Videos saved: {landscape_path}, {vertical_path}")
    mark_used(headline["id"])

    output_paths = [str(landscape_path), str(vertical_path)]

    if do_upload:
        import youtube_upload

        description = f"{script_text}\n\nSource: {headline['link']}\n\n#NigeriaNews #Naija"
        landscape_title = headline["title"][:100]
        video_id = youtube_upload.upload_video(landscape_path, landscape_title, description, privacy="public")
        youtube_upload.set_thumbnail(video_id, thumb_path)

        shorts_title = f"{headline['title'][:90]} #Shorts"
        shorts_description = f"{description}\n\n#Shorts"
        youtube_upload.upload_video(vertical_path, shorts_title, shorts_description, privacy="public")

    return output_paths


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1, help="How many headlines to process")
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube")
    parser.add_argument("--skip-fetch", action="store_true", help="Reuse existing headlines.json")
    args = parser.parse_args()

    if not args.skip_fetch:
        rss_fetch.run()

    with open(config.HEADLINES_FILE, "r", encoding="utf-8") as f:
        headlines = json.load(f)

    priority_rank = {"high": 0, "medium": 1, "low": 2}
    candidates = [h for h in headlines if not h.get("used")]
    candidates.sort(key=lambda x: priority_rank.get(x["priority"], 1))

    if not candidates:
        raise RuntimeError("No unused headlines available.")

    produced = []
    for headline in candidates[: args.count]:
        produced.extend(process_one(headline, args.upload))

    print(f"\n=== Done. {len(produced)} video files produced. ===")
    for p in produced:
        print(" -", p)

    if not produced:
        raise RuntimeError("0 videos were produced — treating as a failed run.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: Pipeline failed: {e}")
        traceback.print_exc()
        sys.exit(1)
        
