"""
Step 1: Pull headlines from all configured Nigerian RSS feeds,
score them by priority, dedupe, and save to output/data/headlines.json
"""
import json
import time
import hashlib
from datetime import datetime, timezone

import feedparser

import config


def score_priority(title: str, summary: str) -> str:
    text = f"{title} {summary}".lower()
    for level in ("high", "medium", "low"):
        for kw in config.PRIORITY_KEYWORDS[level]:
            if kw in text:
                return level
    return "medium"  # default bucket if nothing matches


def _hash_id(title: str, link: str) -> str:
    return hashlib.sha256(f"{title}{link}".encode("utf-8")).hexdigest()[:16]


def fetch_all(max_per_feed: int = 15) -> list[dict]:
    all_items = []
    for source, url in config.RSS_FEEDS.items():
        try:
            parsed = feedparser.parse(url)
        except Exception as e:
            print(f"[WARN] Could not fetch {source}: {e}")
            continue

        if parsed.bozo and not parsed.entries:
            print(f"[WARN] {source} feed looked malformed and returned no entries")
            continue

        for entry in parsed.entries[:max_per_feed]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", "") or entry.get("description", "")
            published = entry.get("published", "") or entry.get("updated", "")
            if not title or not link:
                continue

            item = {
                "id": _hash_id(title, link),
                "source": source,
                "title": title,
                "link": link,
                "summary": summary[:500],
                "published": published,
                "priority": score_priority(title, summary),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "used": False,
            }
            all_items.append(item)

    return all_items


def load_existing() -> dict:
    if config.HEADLINES_FILE.exists():
        with open(config.HEADLINES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {item["id"]: item for item in data}
    return {}


def save(items_by_id: dict):
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    items = sorted(items_by_id.values(), key=lambda x: priority_rank.get(x["priority"], 1))
    with open(config.HEADLINES_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def run(max_per_feed: int = 15) -> list[dict]:
    existing = load_existing()
    fetched = fetch_all(max_per_feed=max_per_feed)

    new_count = 0
    for item in fetched:
        if item["id"] not in existing:
            existing[item["id"]] = item
            new_count += 1

    save(existing)
    print(f"[OK] Fetched {len(fetched)} headlines, {new_count} new. "
          f"Total stored: {len(existing)}")
    return list(existing.values())


if __name__ == "__main__":
    run()
