"""
Simple Gemini client placeholder.
This module supports two modes:
- If GEMINI_API_URL and GEMINI_API_KEY are provided in env, it will POST to that URL with the key in headers.
- Otherwise it provides a mock response to allow local testing.

NOTE: Fill GEMINI_API_URL and GEMINI_API_KEY in environment when you want to call the real Gemini Free API.
"""
import os
import requests

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = os.getenv('GEMINI_API_URL')


def generate_text(prompt: str, max_tokens: int = 512) -> dict:
    """Return dict with keys: { 'text': str, 'raw': object }
    If real API not configured, returns a mock reply.
    """
    if not GEMINI_API_URL or not GEMINI_API_KEY:
        # Mock simple behavior for demo purposes
        # Very naive rule-based responses to help agent logic during development.
        lower = prompt.lower()
        if 'book' in lower and 'appointment' in lower:
            # instruct agent to call tools in order
            return {'text': '{"action": "book_flow"}', 'raw': None}
        if 'who has the most' in lower or 'busiest' in lower:
            return {'text': 'Dr. Amit Patel is busiest next week with 12 appointments.', 'raw': None}
        # default echo
        return {'text': 'I did not find a configured Gemini API key. Running in mock LLM mode.', 'raw': None}

    # If GEMINI values provided, make a generic POST request.
    headers = {'Authorization': f'Bearer {GEMINI_API_KEY}', 'Content-Type': 'application/json'}
    payload = {'prompt': prompt, 'max_tokens': max_tokens}
    try:
        r = requests.post(GEMINI_API_URL, json=payload, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
        # surface top-level text (implementation depends on provider response schema)
        text = data.get('text') or data.get('output') or str(data)
        return {'text': text, 'raw': data}
    except Exception as e:
        return {'text': f'LLM call failed: {e}', 'raw': None}

