"""
Step 3: Convert a script to an MP3 voiceover using edge-tts (free, no API key).
"""
import asyncio
from pathlib import Path

import edge_tts

import config


async def _generate(text: str, out_path: Path, voice: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_path))


def generate_audio(script_text: str, filename: str, voice: str | None = None) -> Path:
    voice = voice or config.TTS_VOICE
    out_path = config.AUDIO_DIR / f"{filename}.mp3"
    asyncio.run(_generate(script_text, out_path, voice))
    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError(f"TTS failed to produce audio at {out_path}")
    return out_path


def list_voices_hint():
    print("Run this in your terminal to see all voices:")
    print("  edge-tts --list-voices")
    print("Nigeria-adjacent options to try: en-GB-RyanNeural, en-US-GuyNeural, "
          "en-NG-EzinneNeural, en-NG-AbeoNeural")


if __name__ == "__main__":
    test_script = (
        "Breaking across Nigeria today. This is a test of the voice pipeline. "
        "Subscribe for daily Nigeria news updates."
    )
    path = generate_audio(test_script, "test_voice")
    print(f"[OK] Saved audio to {path}")
  
