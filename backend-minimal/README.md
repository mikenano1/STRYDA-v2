# STRYDA Backend - Minimal

Minimal FastAPI backend for STRYDA-v2 chat with RAG pipeline.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment (see Configuration section)
cp .env.example .env
# Edit .env with your credentials

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
Ask a question using RAG pipeline.

**Request:**
```json
{
  "query": "What is the minimum cover for apron flashing?",
  "history": [
    {"role": "user", "content": "previous question"},
    {"role": "assistant", "content": "previous answer"}
  ]
}
```

**Response:**
```json
{
  "answer": "Based on NZMRM COP section 4.2.3...",
  "notes": ["retrieval", "backend", "rag"],
  "citations": [
    {
      "doc_id": "uuid-here",
      "source": "NZMRM COP",
      "page": 123,
      "score": 0.856
    }
  ]
}
```

## Configuration

### Environment Variables

Create a `.env` file with the following:

```bash
# Database (Supabase Postgres with pgvector)
DATABASE_URL=postgresql://user:password@host:5432/database

# LLM API Key (choose one)
OPENAI_API_KEY=sk-...
# OR
EMERGENT_LLM_KEY=your-emergent-key
```

### Graceful Fallback

The system gracefully degrades if dependencies are unavailable:

- **No DATABASE_URL**: Returns stub response
- **No LLM Key**: Returns stub response
- **Database error**: Returns stub response
- **LLM error**: Returns context without generation

Frontend always receives a valid response.

## RAG System Architecture

```
Query → Embedding → Vector Search → Context Building → LLM → Response
  │         │              │                │              │        │
  └─────────┴──────────────┴────────────────┴──────────────┴────────┘
                     Graceful fallback if any step fails
```

### Components

#### `rag/db.py`
- Postgres connection management
- Vector similarity search using pgvector
- Returns top-k relevant documents

#### `rag/llm.py`
- OpenAI embedding generation (text-embedding-3-small)
- Chat completion (gpt-4o-mini)
- Handles API errors gracefully

#### `rag/prompt.py`
- System prompt for NZ building codes
- Context formatting from retrieved docs
- Message history management

#### `rag/retriever.py`
- Orchestrates the full RAG pipeline
- Implements graceful fallback logic
- Returns standardized response format

## Database Schema

Expected `documents` table structure:

```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY,
  source TEXT,              -- e.g., "NZMRM COP", "E2/AS1"
  page INTEGER,
  content TEXT,
  embedding VECTOR(1536),   -- OpenAI embedding dimension
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create vector similarity index
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
```

## Development

```bash
# Run with auto-reload
uvicorn app:app --reload --port 8000

# Test health endpoint
curl http://localhost:8000/health

# Test ask endpoint (stub mode - no DB configured)
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"test question"}'

# Test with database configured
export DATABASE_URL="postgresql://..."
export OPENAI_API_KEY="sk-..."
uvicorn app:app --reload --port 8000
```

## Testing Scenarios

### 1. Stub Mode (No Configuration)
```bash
# No .env file
uvicorn app:app
curl -X POST http://localhost:8000/api/ask \
  -d '{"query":"test"}'
# Returns: stub fallback response
```

### 2. RAG Mode (Full Configuration)
```bash
# With DATABASE_URL and OPENAI_API_KEY
curl -X POST http://localhost:8000/api/ask \
  -d '{"query":"minimum apron flashing cover"}'
# Returns: RAG-generated answer with citations
```

### 3. Partial Configuration
```bash
# DATABASE_URL set, no LLM key
# Returns: Context from docs without LLM generation
```

## Dependencies

- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **pydantic** - Data validation
- **psycopg2-binary** - PostgreSQL adapter
- **openai** - LLM and embeddings

## Future Enhancements

- Streaming responses for long answers
- Conversation history persistence
- Multi-turn context management
- Document source filtering
- Caching for common queries
- Rate limiting
- Authentication/authorization
