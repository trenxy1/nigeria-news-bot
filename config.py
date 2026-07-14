"""
Central config for the Nigeria News Bot pipeline.
Edit the values in this file (or set the environment variables) before running.
"""
import os
from pathlib import Path

# ---------- PATHS ----------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "output" / "data"
AUDIO_DIR = BASE_DIR / "output" / "audio"
IMAGE_DIR = BASE_DIR / "output" / "images"
VIDEO_DIR = BASE_DIR / "output" / "videos"

for d in (DATA_DIR, AUDIO_DIR, IMAGE_DIR, VIDEO_DIR):
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

# Keywords used to score priority. Higher score = more likely to be picked
# for a video first. Tune this list as you learn what performs.
PRIORITY_KEYWORDS = {
    "high": ["president", "tinubu", "naira", "senate", "election", "security",
              "police", "military", "boko haram", "bandits", "fuel", "subsidy",
              "cbn", "central bank", "assembly", "governor", "inflation"],
    "medium": ["economy", "business", "court", "minister", "policy", "budget",
                "strike", "protest", "flood", "health"],
    "low": ["sport", "football", "super eagles", "entertainment", "music"],
}

# ---------- LLM PROVIDER (writes the script) ----------
# "gemini" is the default — more generous/reliable free tier than Groq for this job.
# If GEMINI_API_KEY fails or is missing, script_generator.py automatically falls
# back to Groq (if GROQ_API_KEY is set), so one flaky provider doesn't stall the pipeline.
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")  # "gemini" or "groq"

# Get a free key: https://aistudio.google.com/apikey  (Gemini free tier: ~1,500 requests/day)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
)

# Get a free key: https://console.groq.com/keys  (used as fallback if Gemini fails)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

# ---------- TTS (edge-tts, free, no API key) ----------
TTS_VOICE = os.environ.get("TTS_VOICE", "en-GB-RyanNeural")  # try en-NG-EzinneNeural / en-NG-AbeoNeural too

# ---------- IMAGES (Pexels, free tier) ----------
# Get a free key at https://www.pexels.com/api/
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
IMAGE_SEARCH_MAP = {
    "high": "Nigeria government Abuja",
    "medium": "Nigeria economy Lagos business",
    "low": "Nigeria football Super Eagles",
}
IMAGES_PER_VIDEO = 5

# ---------- YOUTUBE ----------
# You need client_secret.json from Google Cloud Console (YouTube Data API v3 enabled).
# See youtube_upload.py for the one-time auth steps.
YOUTUBE_CLIENT_SECRET_FILE = str(BASE_DIR / "client_secret.json")
YOUTUBE_TOKEN_FILE = str(BASE_DIR / "youtube_token.json")
# In GitHub Actions, the token is injected as a secret string instead of a file
# (see .github/workflows/daily-news.yml) — youtube_upload.py checks this first.
YOUTUBE_TOKEN_JSON_ENV = os.environ.get("YOUTUBE_TOKEN_JSON", "")
YOUTUBE_CATEGORY_ID = "25"  # News & Politics
YOUTUBE_DEFAULT_TAGS = ["Nigeria news", "Nigeria today", "Naija news", "Abuja", "Lagos"]
