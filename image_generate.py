"""
Generates AI images tied directly to each scene of a news script, using
Pollinations.ai — a free, no-signup, no-API-key image generation service.

IMPORTANT (news-specific): prompts are built to avoid depicting specific
real, named individuals — the style suffix explicitly steers toward
generic/symbolic/location-based imagery instead. A fabricated "likeness" of
a real politician in a scene that didn't happen is a real credibility and
misinformation risk for a news channel; generic illustrative imagery (a
podium, a government building, a market scene) avoids that while still
looking relevant to the story.

Requests are made ONE AT A TIME with spacing and retry-with-backoff on 429 —
Pollinations' free tier rate-limits aggressively on parallel requests.
"""
import time
import random
import urllib.parse
from pathlib import Path

import requests

import config

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"

DELAY_BETWEEN_REQUESTS = 4.0
MAX_RETRIES = 4
BACKOFF_BASE = 6.0


def _generate_one(prompt: str, width: int, height: int, out_path: Path, timeout: int = 90) -> Path:
    full_prompt = f"{prompt}, {config.IMAGE_STYLE_SUFFIX}"
    encoded = urllib.parse.quote(full_prompt)
    url = POLLINATIONS_URL.format(prompt=encoded)
    params = {"width": width, "height": height, "nologo": "true"}

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            if resp.status_code == 429:
                wait = BACKOFF_BASE * (2 ** (attempt - 1)) + random.uniform(0, 2)
                print(f"    [429] rate limited, attempt {attempt}/{MAX_RETRIES}, "
                      f"waiting {wait:.1f}s before retry...")
                time.sleep(wait)
                continue

            resp.raise_for_status()
            out_path.write_bytes(resp.content)

            if out_path.stat().st_size < 1000:
                raise RuntimeError("response too small, likely an error page not an image")

            return out_path

        except requests.exceptions.HTTPError as e:
            last_error = e
            if getattr(e.response, "status_code", None) == 429:
                wait = BACKOFF_BASE * (2 ** (attempt - 1)) + random.uniform(0, 2)
                print(f"    [429 via exception] attempt {attempt}/{MAX_RETRIES}, waiting {wait:.1f}s...")
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            last_error = e
            wait = BACKOFF_BASE * (2 ** (attempt - 1)) + random.uniform(0, 2)
            print(f"    [WARN] attempt {attempt}/{MAX_RETRIES} failed ({e}), waiting {wait:.1f}s...")
            time.sleep(wait)

    raise RuntimeError(f"Failed after {MAX_RETRIES} attempts for prompt '{prompt[:60]}...': {last_error}")


def generate_images_for_scenes(scenes: list[str], story_id: str, width: int, height: int,
                                max_workers: int = 1) -> list[Path]:
    """max_workers is accepted for backward compatibility but ignored —
    requests are always sequential (parallel requests get rate-limited)."""
    story_dir = config.IMAGE_DIR / story_id
    story_dir.mkdir(parents=True, exist_ok=True)

    results: list[Path] = []
    errors: list[str] = []

    for idx, scene_text in enumerate(scenes):
        out_path = story_dir / f"scene_{idx:03d}.jpg"
        print(f"  Generating image {idx + 1}/{len(scenes)}...")
        try:
            path = _generate_one(scene_text, width, height, out_path)
            results.append(path)
        except Exception as e:
            errors.append(str(e))
            print(f"  [WARN] Giving up on scene {idx + 1}: {e}")

        if idx < len(scenes) - 1:
            time.sleep(DELAY_BETWEEN_REQUESTS)

    if not results:
        raise RuntimeError("All image generations failed:\n" + "\n".join(errors))

    if errors:
        print(f"[WARN] {len(errors)}/{len(scenes)} scenes failed to generate an image "
              f"and were skipped.")

    return results


if __name__ == "__main__":
    test_scenes = [
        "a government building exterior with a Nigerian flag",
        "a busy Lagos market street scene",
    ]
    paths = generate_images_for_scenes(test_scenes, "test_story", width=1920, height=1080)
    print(f"[OK] Generated {len(paths)} images:")
    for p in paths:
        print(" -", p)
                                       
