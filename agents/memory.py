from datetime import date
from db.client import supabase
from utils.embeddings import get_embedding


def run_memory(structured: dict) -> None:
    name = structured.get("name", "")
    company = structured.get("company", "") or ""

    existing = (
        supabase.table("contacts")
        .select("*")
        .ilike("name", name)
        .ilike("company", company)
        .execute()
    )

    if existing.data:
        contact_id = existing.data[0]["id"]
        supabase.table("contacts").update({"updated_at": date.today().isoformat()}).eq(
            "id", contact_id
        ).execute()
    else:
        result = (
            supabase.table("contacts")
            .insert(
                {
                    "name": name,
                    "company": company,
                    "role": structured.get("role"),
                    "email": structured.get("email"),
                    "last_contact": structured.get("date"),
                }
            )
            .execute()
        )
        contact_id = result.data[0]["id"]

    supabase.table("interactions").insert(
        {
            "contact_id": contact_id,
            "date": structured.get("date"),
            "topic": structured.get("topic"),
            "summary": structured.get("summary"),
            "next_steps": structured.get("next_steps"),
            "sentiment": structured.get("sentiment"),
        }
    ).execute()

    content = (
        f"{name} at {company}. "
        f"{structured.get('topic', '')}. "
        f"{structured.get('summary', '')}. "
        f"Next: {structured.get('next_steps', '')}"
    )
    embedding = get_embedding(content)

    supabase.table("memories").insert(
        {"contact_id": contact_id, "content": content, "embedding": embedding}
    ).execute()
