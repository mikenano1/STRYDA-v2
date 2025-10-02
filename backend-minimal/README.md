# STRYDA Backend - Minimal

Minimal FastAPI backend for STRYDA-v2 chat.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints

### GET /health
Health check endpoint.

**Response:**
```json
{
  "ok": true,
  "version": "v0.1",
  "time": "2025-10-02T09:00:00.000000"
}
```

### POST /api/ask
Ask a question (currently returns stub response).

**Request:**
```json
{
  "query": "minimum apron flashing cover"
}
```

**Response:**
```json
{
  "answer": "Coming soon - this is a backend stub response for your query.",
  "notes": ["demo", "backend"],
  "citation": "NZMRM COP X.Y"
}
```

## Development

```bash
# Run with auto-reload
uvicorn app:app --reload --port 8000

# Test health endpoint
curl http://localhost:8000/health

# Test ask endpoint
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"test question"}'
```

## Future Features

- RAG integration with building code database
- Real-time citations
- Multi-turn conversation context
- User session management
