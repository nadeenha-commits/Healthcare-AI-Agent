import os
import requests


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
GEMINI_API_URL = os.getenv("GEMINI_API_URL") or (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
)


def generate_text(prompt: str, max_tokens: int = 512) -> dict:
    """
    Calls the Gemini generateContent REST API.

    Returns:
    {
        "text": str,
        "raw": object
    }

    If GEMINI_API_KEY is missing, returns a local mock response so the project
    can still run in demo/dev mode.
    """
    if not GEMINI_API_KEY:
        return _mock_response(prompt)

    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json",
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
            "temperature": 0.2,
        },
    }

    try:
        response = requests.post(
            GEMINI_API_URL,
            headers=headers,
            json=payload,
            timeout=20,
        )
        response.raise_for_status()

        data = response.json()
        text = _extract_text(data)

        return {
            "text": text,
            "raw": data,
        }

    except Exception as exc:
        return {
            "text": f"LLM call failed: {exc}",
            "raw": None,
        }


def _extract_text(data: dict) -> str:
    """
    Extracts the text from Gemini generateContent response.
    """
    try:
        candidates = data.get("candidates", [])
        if not candidates:
            return ""

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        if not parts:
            return ""

        return parts[0].get("text", "")

    except Exception:
        return str(data)


def _mock_response(prompt: str) -> dict:
    """
    Local fallback for development when GEMINI_API_KEY is not configured.
    Keeps the project demo working without external API calls.
    """
    lower = prompt.lower()

    if "book" in lower and "appointment" in lower:
        return {
            "text": '{"action": "book_flow"}',
            "raw": None,
        }

    if "search patient" in lower or "find patient" in lower:
        return {
            "text": '{"action": "search_patient", "args": {"query": "Sarah Cohen"}}',
            "raw": None,
        }

    if "list doctors" in lower or "show doctors" in lower:
        return {
            "text": '{"action": "list_doctors", "args": {}}',
            "raw": None,
        }

    if "busiest doctor" in lower or "most appointments" in lower:
        return {
            "text": '{"action": "busiest_doctor", "args": {}}',
            "raw": None,
        }

    if "department load" in lower:
        return {
            "text": '{"action": "department_load", "args": {}}',
            "raw": None,
        }

    return {
        "text": "I am running in mock LLM mode because GEMINI_API_KEY is not configured.",
        "raw": None,
    }