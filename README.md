# Mnemosyne
Three-agent relationship memory system for M&A contexts.
Intake → Memory → Retrieval. Powered by Claude + Supabase pgvector.

## Setup
1. Copy .env.example to .env and fill in credentials
2. Run schema.sql in your Supabase SQL editor
3. pip install -r requirements.txt

## Usage
python main.py ingest "Had a call with Sarah Chen from Lazard..."
python main.py query "Who do I know at bulge brackets?"

## UI

### UI
pip install fastapi uvicorn
python -m uvicorn ui.server:app --reload --port 8000
Open http://localhost:8000
