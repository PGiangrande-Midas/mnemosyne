import json
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

_SYSTEM = (
    "You are a contact extraction agent for an M&A relationship database. "
    "Given unstructured input (email, note, voice transcript), extract: "
    "name, company, role, email, date (ISO string only if a specific date is explicitly stated in the text, otherwise null — do NOT infer or guess), topic (max 10 words), "
    "summary (max 2 sentences), next_steps (string or null), "
    "sentiment (positive | neutral | negative). "
    "Return ONLY valid JSON. No explanation. No preamble."
)


def run_intake(raw_text: str) -> dict:
    message = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=_SYSTEM,
        messages=[{"role": "user", "content": raw_text}],
    )
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0].strip()
    return json.loads(text)
