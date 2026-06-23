import os
import time
from typing import Any, Dict

import requests


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
GEMINI_API_URL = os.getenv("GEMINI_API_URL") or (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
)


def generate_text(prompt: str, max_tokens: int = 512) -> Dict[str, Any]:
    """
    Calls the real Gemini API.

    This function does not return hardcoded AI answers.
    It sends the prompt to Gemini and returns Gemini's real response.

    If Gemini is temporarily unavailable, it retries a few times.
    """
    if not GEMINI_API_KEY:
        return {
            "text": "Gemini API is not configured. Please set GEMINI_API_KEY.",
            "raw": None,
            "error": "missing_api_key",
        }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY,
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt,
                    }
                ]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.3,
        },
    }

    last_error = ""

    for attempt in range(3):
        try:
            response = requests.post(
                GEMINI_API_URL,
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code in {429, 500, 502, 503, 504}:
                last_error = f"{response.status_code} {response.text}"
                time.sleep(1.5 * (attempt + 1))
                continue

            response.raise_for_status()

            data = response.json()
            text = _extract_text(data)

            if not text:
                return {
                    "text": "Gemini returned an empty response.",
                    "raw": data,
                    "error": "empty_response",
                }

            return {
                "text": text,
                "raw": data,
                "error": None,
            }

        except requests.RequestException as exc:
            last_error = str(exc)
            time.sleep(1.5 * (attempt + 1))

    return {
        "text": (
            "Gemini is temporarily unavailable after several retries. "
            "Please try again shortly."
        ),
        "raw": None,
        "error": last_error or "gemini_unavailable",
    }


def _extract_text(data: Dict[str, Any]) -> str:
    candidates = data.get("candidates", [])

    if not candidates:
        return ""

    content = candidates[0].get("content", {})
    parts = content.get("parts", [])

    text_parts = []

    for part in parts:
        text = part.get("text")
        if text:
            text_parts.append(text)

    return "\n".join(text_parts).strip()