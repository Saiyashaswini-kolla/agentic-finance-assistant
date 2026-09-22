"""Thin LLM wrapper (Gemini). Returns None when no API key is set or the call fails."""
import os

STATS = {"ok": 0, "failed": 0}   # counts real Gemini answers vs fallbacks


def complete(system: str, prompt: str, max_tokens: int = 1000):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=60000))
        resp = client.models.generate_content(
            model=os.getenv("MODEL", "gemini-3.6-flash"),
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
            ),
        )
        text = resp.text or None
        STATS["ok" if text else "failed"] += 1
        return text
    except Exception as e:
        STATS["failed"] += 1
        print(f"Gemini call failed, using offline mode instead: {str(e)[:150]}")
        return None
