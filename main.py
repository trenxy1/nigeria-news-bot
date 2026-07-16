"""
Orchestrator: runs the full pipeline end to end for N top-priority headlines.

Usage:
    py main.py                # process 1 headline, save video locally, no upload
    py main.py --count 3      # process 3 headlines
    py main.py --upload       # also upload to YouTube as UNLISTED (review before public)
"""
import argparse
import json
import traceback
from datetime import date

import config
import rss_fetch
import script_generator
import tts_generator
import image_fetch
import video_builder


def mark_used(headline_id: str):
    with open(config.HEADLINES_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)
    for item in items:
        if item["id"] == headline_id:
            item["used"] = True
    with open(config.HEADLINES_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def process_one(headline: dict, do_upload: bool) -> str | None:
    print(f"\n=== {headline['title']} ({headline['priority']}) ===")

    print("[1/4] Generating script with Groq...")
    script_text = script_generator.generate_script(headline)
    print(script_text)

    print("[2/4] Generating voiceover...")
    audio_path = tts_generator.generate_audio(script_text, headline["id"])

    print("[3/4] Fetching images...")
    images = image_fetch.fetch_images(headline["priority"], headline["id"])

    print("[4/4] Building video...")
    out_name = f"{date.today().isoformat()}_{headline['id']}.mp4"
    output_path = config.VIDEO_DIR / out_name
    video_builder.build_video(images, audio_path, script_text, headline["title"], output_path)
    print(f"[OK] Video saved: {output_path}")

    mark_used(headline["id"])

    if do_upload:
        import youtube_upload
        description = f"{script_text}\n\nSource: {headline['link']}\n\n#NigeriaNews #Naija"
        title = f"Nigeria News: {headline['title'][:80]}"
        youtube_upload.upload_video(output_path, title, description, privacy="public")

    return str(output_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1, help="How many videos to produce")
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube as unlisted")
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
        print("No unused headlines available. Run without --skip-fetch to pull fresh ones.")
        return

    produced = []
    for headline in candidates[: args.count]:
        try:
            path = process_one(headline, args.upload)
            produced.append(path)
        except Exception as e:
            print(f"[ERROR] Failed on '{headline['title']}': {e}")
            traceback.print_exc()

    print(f"\n=== Done. {len(produced)}/{args.count} videos produced. ===")
    for p in produced:
        print(" -", p)


if __name__ == "__main__":
    main()
  
