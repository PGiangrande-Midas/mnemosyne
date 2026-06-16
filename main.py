import sys
import truststore
truststore.inject_into_ssl()
from dotenv import load_dotenv

load_dotenv()

from metis import track

from agents.intake import run_intake
from agents.memory import run_memory
from agents.retrieval import run_retrieval

# Observability only. The track() wrapper records each memory operation through
# Metis (shared Supabase runs table) so Mnemosyne appears in the dashboard
# alongside the other Pantheon agents. The core memory logic is unchanged.
INGEST_CRITERIA = (
    "Extract the contact's structured fields from the raw text and persist them "
    "to memory accurately, without inventing details or losing key facts."
)
QUERY_CRITERIA = (
    "Answer the question using only what is stored in memory, grounded in the "
    "retrieved contacts, with no fabrication."
)


def ingest(text: str) -> dict:
    with track(
        agent="mnemosyne",
        task="ingest: " + text,
        success_criteria=INGEST_CRITERIA,
        input={"mode": "ingest", "text": text},
        tags=["mnemosyne", "memory", "ingest"],
    ) as run:
        structured = run_intake(text)
        run_memory(structured)
        run.set_output(structured)
        filled = [k for k, v in structured.items() if v not in (None, "")]
        run.set_metrics(
            operation="ingest",
            fields_extracted=len(filled),
            has_name=bool(structured.get("name")),
            has_company=bool(structured.get("company")),
            sentiment=structured.get("sentiment"),
        )
        return structured


def query(text: str) -> str:
    with track(
        agent="mnemosyne",
        task="query: " + text,
        success_criteria=QUERY_CRITERIA,
        input={"mode": "query", "query": text},
        tags=["mnemosyne", "memory", "query"],
    ) as run:
        answer = run_retrieval(text)
        run.set_output(answer)
        run.set_metrics(
            operation="query",
            answer_chars=len(answer),
            contacts_found=not answer.strip().lower().startswith("no relevant contacts"),
        )
        return answer


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print('  python main.py ingest "Raw text here"')
        print('  python main.py query "Your question here"')
        sys.exit(1)

    mode = sys.argv[1]
    text = sys.argv[2]

    if mode == "ingest":
        structured = ingest(text)
        print(f"Stored: {structured.get('name')} at {structured.get('company')}")

    elif mode == "query":
        answer = query(text)
        print(answer)

    else:
        print(f"Unknown mode: {mode}. Use 'ingest' or 'query'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
