import truststore
truststore.inject_into_ssl()

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agents.intake import run_intake
from agents.memory import run_memory
from agents.retrieval import run_retrieval
from db.client import supabase

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UI_DIR = Path(__file__).parent


class IngestRequest(BaseModel):
    text: str


@app.post("/ingest")
def ingest(req: IngestRequest):
    structured = run_intake(req.text)
    run_memory(structured)
    return {"name": structured.get("name"), "company": structured.get("company")}


@app.get("/query")
def query_endpoint(q: str = Query(...)):
    answer = run_retrieval(q)
    return {"answer": answer}


@app.get("/contacts")
def contacts():
    rows = (
        supabase.table("contacts")
        .select("*")
        .order("updated_at", desc=True)
        .execute()
    )
    result = []
    for contact in rows.data:
        interactions = (
            supabase.table("interactions")
            .select("*")
            .eq("contact_id", contact["id"])
            .order("date", desc=True)
            .execute()
        )
        result.append({**contact, "interactions": interactions.data})
    return result


@app.delete("/contacts/{contact_id}")
def delete_contact(contact_id: str):
    supabase.table("memories").delete().eq("contact_id", contact_id).execute()
    supabase.table("interactions").delete().eq("contact_id", contact_id).execute()
    supabase.table("contacts").delete().eq("id", contact_id).execute()
    return {"ok": True}


@app.get("/")
def index():
    return FileResponse(UI_DIR / "index.html")
