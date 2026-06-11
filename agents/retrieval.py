import ast
import json
import math
import os
import anthropic
from dotenv import load_dotenv

from db.client import supabase
from utils.embeddings import get_embedding

load_dotenv()

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

_SYSTEM = (
    "You are a relationship retrieval agent for an M&A boutique. "
    "Answer in 1-2 sentences max. Lead with names and firms. "
    "No preamble, no filler, no hedging."
)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def run_retrieval(query: str) -> str:
    query_embedding = get_embedding(query)

    rows = supabase.table("memories").select("id, contact_id, content, embedding").execute()

    scored = []
    for row in rows.data:
        stored = row["embedding"]
        if isinstance(stored, str):
            stored = ast.literal_eval(stored)
        sim = _cosine_similarity(query_embedding, stored)
        scored.append((sim, row))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [item for item in scored[:5] if item[0] >= 0.30]
    if not top:
        return "No relevant contacts found for that query."

    contact_ids = list({row["contact_id"] for _, row in top})
    contacts = (
        supabase.table("contacts").select("*").in_("id", contact_ids).execute()
    )

    memories_context = [
        {"content": row["content"], "similarity": round(sim, 4)}
        for sim, row in top
    ]
    context = json.dumps(
        {"memories": memories_context, "contacts": contacts.data}, indent=2
    )

    message = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=_SYSTEM,
        messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuery: {query}"}],
    )
    return message.content[0].text
