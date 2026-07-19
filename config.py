"""
Central config for the Nigeria News Bot pipeline.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "output" / "data"
AUDIO_DIR = BASE_DIR / "output" / "audio"
IMAGE_DIR = BASE_DIR / "output" / "images"
VIDEO_DIR = BASE_DIR / "output" / "videos"
THUMBNAIL_DIR = BASE_DIR / "output" / "thumbnails"

for d in (DATA_DIR, AUDIO_DIR, IMAGE_DIR, VIDEO_DIR, THUMBNAIL_DIR):
    d.mkdir(parents=True, exist_ok=True)

HEADLINES_FILE = DATA_DIR / "headlines.json"

# ---------- RSS FEEDS ----------
RSS_FEEDS = {
    "Punch Nigeria": "https://punchng.com/feed",
    "Vanguard": "https://www.vanguardngr.com/feed",
    "Guardian Nigeria": "https://guardian.ng/feed",
    "Premium Times": "https://www.premiumtimesng.com/feed",
    "Sahara Reporters": "https://saharareporters.com/feeds/news",
    "Channels TV": "https://www.channelstv.com/feed",
    "Leadership Newspaper": "https://leadership.ng/feed",
}

PRIORITY_KEYWORDS = {
    "high": ["president", "tinubu", "naira", "senate", "election", "security",
              "police", "military", "boko haram", "bandits", "fuel", "subsidy",
              "cbn", "central bank", "assembly", "governor", "inflation"],
    "medium": ["economy", "business", "court", "minister", "policy", "budget",
                "strike", "protest", "flood", "health"],
    "low": ["sport", "football", "super eagles", "entertainment", "music"],
}

# ---------- LLM PROVIDER ----------
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

SYSTEM_PROMPT = """You are a Nigeria national news anchor. Write a script for
narration, roughly 130-250 words (60-120 seconds spoken aloud).

RULES:
- Start with a strong hook: "Breaking across Nigeria..." or "In Abuja today..."
- Cover: who, what, when, where, why it matters nationally
- Add context: How does this affect everyday Nigerians? Economy? Security?
- Use Nigerian context: mention states, regions, or ethnic angles where relevant
- End with: "Subscribe for daily Nigeria news updates."
- Neutral, factual tone. No speculation. No partisan bias.
- If story involves Naira amounts, write them out clearly.
- If story involves a location, mention the state.
- Write in short, concrete, filmable sentences — each sentence should evoke
  a clear visual (a building, a crowd, a document, a location), since each
  sentence becomes its own AI-generated illustration.
- Output ONLY the script text. No preamble, no markdown, no labels.
"""

# ---------- TTS ----------
TTS_VOICE = os.environ.get("TTS_VOICE", "en-GB-RyanNeural")
TTS_RATE = os.environ.get("TTS_RATE", "+0%")

# ---------- AI IMAGE GENERATION (Pollinations.ai — free, no API key) ----------
# IMPORTANT: this style suffix deliberately steers toward generic, symbolic,
# location-based imagery rather than depicting specific real people. A
# fabricated "photo" of a real named politician in a scene that didn't
# happen is a misinformation and channel-safety risk — generic illustrative
# imagery (a podium, a government building, a market scene, a flag) still
# looks relevant to the story without that risk.
IMAGE_STYLE_SUFFIX = (
    "photojournalistic style, realistic, natural lighting, high detail, "
    "documentary photography, generic illustrative scene, no specific "
    "recognizable individual's face, wide shot or symbolic imagery, 4k quality"
)
IMAGE_GEN_MAX_WORKERS = 1

# ---------- YOUTUBE ----------
YOUTUBE_CLIENT_SECRET_FILE = str(BASE_DIR / "client_secret.json")
YOUTUBE_TOKEN_FILE = str(BASE_DIR / "youtube_token.json")
YOUTUBE_TOKEN_JSON_ENV = os.environ.get("YOUTUBE_TOKEN_JSON", "")
YOUTUBE_CATEGORY_ID = "25"  # News & Politics
YOUTUBE_DEFAULT_TAGS = ["Nigeria news", "Nigeria today", "Naija news", "Abuja", "Lagos"]
