"""
Converts a story script to an MP3 voiceover using edge-tts, AND captures the
exact spoken timestamp of every word (via edge-tts's WordBoundary events).
This timing data is what lets captions/images align to the real audio
instead of an estimated proportion — no drift over long videos.

Retries the whole generation if boundaries come back empty — this is usually
a transient websocket hiccup talking to Microsoft's TTS service, not a real
failure, and a retry resolves it most of the time.
"""
import asyncio
import time
from pathlib import Path

import edge_tts

import config

MAX_ATTEMPTS = 3
RETRY_DELAY = 5.0  # seconds between attempts


async def _generate(text: str, out_path: Path, voice: str, rate: str) -> list[dict]:
    communicate = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    boundaries = []

    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 10_000_000
                end = (chunk["offset"] + chunk["duration"]) / 10_000_000
                boundaries.append({"word": chunk["text"], "start": start, "end": end})

    return boundaries


def generate_audio_with_timing(script_text: str, filename: str, voice: str | None = None,
                                rate: str | None = None) -> tuple[Path, list[dict]]:
    """Returns (audio_path, word_boundaries). Retries up to MAX_ATTEMPTS times
    if the TTS stream comes back without word-timing data (usually a
    transient connection issue, not a real failure)."""
    voice = voice or config.TTS_VOICE
    rate = rate or config.TTS_RATE
    out_path = config.AUDIO_DIR / f"{filename}.mp3"

    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            boundaries = asyncio.run(_generate(script_text, out_path, voice, rate))

            if not out_path.exists() or out_path.stat().st_size == 0:
                raise RuntimeError("TTS produced no audio file")

            if not boundaries:
                raise RuntimeError("TTS produced audio but no word-timing data came back")

            return out_path, boundaries

        except Exception as e:
            last_error = e
            print(f"[WARN] TTS attempt {attempt}/{MAX_ATTEMPTS} failed for '{filename}': {e}")
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_DELAY)

    raise RuntimeError(
        f"TTS failed after {MAX_ATTEMPTS} attempts for '{filename}': {last_error}"
    )


def generate_audio(script_text: str, filename: str, voice: str | None = None,
                    rate: str | None = None) -> Path:
    """Simple wrapper for callers that only need the audio file, no timing."""
    path, _ = generate_audio_with_timing(script_text, filename, voice, rate)
    return path


if __name__ == "__main__":
    test_script = "The house was quiet. Too quiet. Then, from upstairs, a floorboard creaked."
    path, boundaries = generate_audio_with_timing(test_script, "test_voice")
    print(f"[OK] Saved audio to {path}")
    print(f"[OK] Got {len(boundaries)} word timings:")
    for b in boundaries:
        print(f"  {b['start']:.2f}-{b['end']:.2f}s: {b['word']}")
            
