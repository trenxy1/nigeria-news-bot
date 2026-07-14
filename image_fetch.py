"""
Step 4: Pull relevant images for a story from Pexels (free tier, needs API key).
"""
from pathlib import Path
import requests

import config

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"


def fetch_images(priority: str, story_id: str, count: int | None = None) -> list[Path]:
    if not config.PEXELS_API_KEY:
        raise RuntimeError(
            "PEXELS_API_KEY is not set. Get a free key at https://www.pexels.com/api/ "
            "and set it as an environment variable or in config.py"
        )

    count = count or config.IMAGES_PER_VIDEO
    query = config.IMAGE_SEARCH_MAP.get(priority, "Nigeria news")

    headers = {"Authorization": config.PEXELS_API_KEY}
    params = {"query": query, "per_page": count, "orientation": "landscape"}

    resp = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    photos = data.get("photos", [])
    if not photos:
        raise RuntimeError(f"No Pexels images found for query '{query}'")

    saved_paths = []
    story_dir = config.IMAGE_DIR / story_id
    story_dir.mkdir(parents=True, exist_ok=True)

    for i, photo in enumerate(photos):
        img_url = photo["src"]["large"]
        img_resp = requests.get(img_url, timeout=30)
        img_resp.raise_for_status()
        img_path = story_dir / f"img_{i}.jpg"
        img_path.write_bytes(img_resp.content)
        saved_paths.append(img_path)

    return saved_paths


if __name__ == "__main__":
    paths = fetch_images("high", "test_story")
    print(f"[OK] Downloaded {len(paths)} images:")
    for p in paths:
        print(" -", p)
      
