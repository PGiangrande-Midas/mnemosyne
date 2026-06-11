import sys
import truststore
truststore.inject_into_ssl()
from dotenv import load_dotenv

load_dotenv()

from agents.intake import run_intake
from agents.memory import run_memory
from agents.retrieval import run_retrieval


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print('  python main.py ingest "Raw text here"')
        print('  python main.py query "Your question here"')
        sys.exit(1)

    mode = sys.argv[1]
    text = sys.argv[2]

    if mode == "ingest":
        structured = run_intake(text)
        run_memory(structured)
        print(f"Stored: {structured.get('name')} at {structured.get('company')}")

    elif mode == "query":
        answer = run_retrieval(text)
        print(answer)

    else:
        print(f"Unknown mode: {mode}. Use 'ingest' or 'query'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
