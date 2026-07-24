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

# "high" bumped with more crime/security terms — this channel's own
# analytics show crime/arrest stories dramatically outperforming policy
# stories (e.g. an arrest story got 331 views vs 127 for a policy story),
# so these get selected first more often.
PRIORITY_KEYWORDS = {
    "high": ["president", "tinubu", "naira", "senate", "election", "security",
              "police", "military", "boko haram", "bandits", "fuel", "subsidy",
              "cbn", "central bank", "assembly", "governor", "inflation",
              "arrest", "arrested", "kidnap", "kidnapped", "abduct", "abducted",
              "cult", "cultist", "gunmen", "killed", "attack", "robbery",
              "rescue", "rescued", "manhunt", "wanted"],
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

# This teaser prompt mirrors the horror bot's working pattern: a short cut
# FROM the full script (not an independent piece), withholding a specific
# detail, driving the viewer to the full video. Fixes the funnel problem
# where Shorts previously contained the whole story with no reason to click
# through — Shorts got 561 views vs 41 for long-form on nearly equal output.
SYSTEM_PROMPT_TEASER = """You are cutting a short, high-curiosity teaser from
a Nigeria news script, to hook viewers into watching the full story on the
main channel. Target: 60-90 words, roughly 25-40 seconds spoken aloud.

You will be given the FULL SCRIPT TEXT. Do not write new content — extract
or lightly rework the single most attention-grabbing fact or detail from it
(often the "what happened" hook, or the most striking specific detail — NOT
every fact, and not the full resolution/outcome if there is one).

RULES:
- Open with the strongest hook from the story — the first sentence must
  grab attention immediately.
- Include enough real information to be genuinely informative on its own
  (this is news, not clickbait) — but deliberately leave out at least one
  specific detail (an exact figure, a name, an outcome) that the full video
  covers.
- End with a brief, natural call-to-action: "Full story on the channel" or
  similar — one short sentence.
- Same neutral, factual, non-partisan tone as the full script.
- Output ONLY the teaser text. No preamble, no markdown, no labels.
"""

# ---------- TTS ----------
TTS_VOICE = os.environ.get("TTS_VOICE", "en-GB-RyanNeural")
TTS_RATE = os.environ.get("TTS_RATE", "+0%")

# ---------- AI IMAGE GENERATION (Pollinations.ai — free, no API key) ----------
# Deliberately steers toward generic, symbolic, location-based imagery
# rather than depicting specific real people — see prior discussion: a
# fabricated "photo" of a real named politician in a scene that didn't
# happen is a misinformation and channel-safety risk.
IMAGE_STYLE_SUFFIX = (
    "photojournalistic style, realistic, natural lighting, high detail, "
    "documentary photography, generic illustrative scene, no specific "
    "recognizable individual's face, wide shot or symbolic imagery, 4k quality"
)
IMAGE_GEN_MAX_WORKERS = 1

# ---------- END-CARD / SUBSCRIBE PROMPT ----------
SUBSCRIBE_CTA_TEXT = "SUBSCRIBE to NewsUpdate for daily Nigeria news"
SUBSCRIBE_CTA_DURATION = 4.0  # seconds shown at the end of each video

# ---------- YOUTUBE ----------
YOUTUBE_CLIENT_SECRET_FILE = str(BASE_DIR / "client_secret.json")
YOUTUBE_TOKEN_FILE = str(BASE_DIR / "youtube_token.json")
YOUTUBE_TOKEN_JSON_ENV = os.environ.get("YOUTUBE_TOKEN_JSON", "")
YOUTUBE_CATEGORY_ID = "25"  # News & Politics
YOUTUBE_DEFAULT_TAGS = ["Nigeria news", "Nigeria today", "Naija news", "Abuja", "Lagos"]
