"""
Step 2: Turn a headline + summary into a broadcast-ready script.

Tries Gemini first (default, free tier: https://aistudio.google.com/apikey).
If that fails or isn't configured, automatically falls back to Groq
(https://console.groq.com/keys) so one flaky provider doesn't stall the pipeline.
"""
import json
import requests

import config


def _build_user_prompt(headline: dict) -> str:
    return (
        f"Headline: {headline['title']}\n"
        f"Source: {headline['source']}\n"
        f"Summary: {headline.get('summary', '')}\n\n"
        f"Write the news script now."
    )


def _generate_gemini(headline: dict, timeout: int) -> str:
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    payload = {
        "system_instruction": {"parts": [{"text": config.SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": _build_user_prompt(headline)}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 600},
    }
    resp = requests.post(
        f"{config.GEMINI_URL}?key={config.GEMINI_API_KEY}",
        json=payload, timeout=timeout,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Gemini response shape: {data}") from e


def _generate_groq(headline: dict, timeout: int) -> str:
    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")

    payload = {
        "model": config.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(headline)},
        ],
        "temperature": 0.4,
        "max_tokens": 600,
    }
    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    resp = requests.post(config.GROQ_URL, headers=headers, json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"Groq API error {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def generate_script(headline: dict, timeout: int = 60) -> str:
    providers = (
        [_generate_gemini, _generate_groq]
        if config.LLM_PROVIDER == "gemini"
        else [_generate_groq, _generate_gemini]
    )

    errors = []
    for provider_fn in providers:
        try:
            script = provider_fn(headline, timeout)
            if script:
                return script
        except Exception as e:
            errors.append(f"{provider_fn.__name__}: {e}")
            print(f"[WARN] {provider_fn.__name__} failed, trying next provider: {e}")

    raise RuntimeError(
        "All LLM providers failed for '" + headline["title"] + "':\n" + "\n".join(errors)
    )


if __name__ == "__main__":
    with open(config.HEADLINES_FILE, "r", encoding="utf-8") as f:
        headlines = json.load(f)
    if not headlines:
        print("No headlines found. Run rss_fetch.py first.")
    else:
        script = generate_script(headlines[0])
        print("---- GENERATED SCRIPT ----")
        print(script)
