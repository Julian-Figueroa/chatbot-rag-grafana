# Grafana RAG Chatbot + Observability

A production-grade RAG chatbot that answers questions **about Grafana**, monitored **in Grafana**. Built as a portfolio project demonstrating FDE-level engineering: real instrumentation, real observability, real data.

## Architecture

```mermaid
graph LR
    User -->|question| Gradio[Gradio UI\n:7860]
    Gradio -->|POST /chat| FastAPI[FastAPI\n:8000]
    FastAPI -->|embed + search| ChromaDB[(ChromaDB)]
    FastAPI -->|completion| OpenAI[OpenAI\ngpt-4o-mini]
    FastAPI -->|expose /metrics| Prometheus[Prometheus\n:9090]
    Prometheus -->|scrape| Grafana[Grafana\n:3000]
```

## Phase 2 Features

Phase 2 adds four production-oriented capabilities on top of the core RAG pipeline:

| Feature | What it does |
|---|---|
| **Conversation Memory** | LangChain `ConversationBufferMemory` keyed by `session_id` — each session keeps its own history so follow-up questions work naturally |
| **Feedback Loop** | Thumbs 👍/👎 in the Gradio UI POST to `/feedback`, incrementing a `rag_feedback_total{rating}` Prometheus counter visible in the Token Usage dashboard |
| **Cross-encoder Reranking** | After ChromaDB returns k=6 candidates, `cross-encoder/ms-marco-MiniLM-L-6-v2` rescores and keeps the top 3 — improving answer quality without extra API calls |
| **API Key Auth** | `/chat` requires an `X-API-Key` header; set `API_KEY` in `.env` (defaults to `dev-key-123` in development) |

![Gradio Chatbot UI](data/readme/phase-2/gradio-chatbot.png)

![Token Usage & Feedback Dashboard](data/readme/phase-2/tokens-usage-up-down.png)

## Quick Start

### 1. Prerequisites

- Docker + Docker Compose
- OpenAI API key

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Download and index Grafana docs

```bash
pip install langchain-community langchain-openai langchain-chroma chromadb openai pydantic-settings python-dotenv
python scripts/download_docs.py
python scripts/ingest_docs.py
```

### 4. Start all services

```bash
docker compose up --build
```

### 5. Verify

```bash
# Health check
curl localhost:8000/health
# Expected: {"status":"ok","chroma_doc_count":N}

# Custom metrics present
curl localhost:8000/metrics | grep rag_

# Chat endpoint (X-API-Key required — matches API_KEY in .env)
curl -X POST localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-123" \
  -d '{"question": "What is Grafana Loki?"}'

# Multi-turn: follow-up with the same session_id
curl -X POST localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-123" \
  -d '{"question": "How does it compare to Elasticsearch?", "session_id": "test-session"}'

# Submit feedback (rating: up or down)
curl -X POST "localhost:8000/feedback?session_id=test-session&rating=up"
```

| Service    | URL                   |
| ---------- | --------------------- |
| Chatbot UI | http://localhost:7860 |
| API        | http://localhost:8000 |
| Prometheus | http://localhost:9090 |
| Grafana    | http://localhost:3000 |

Grafana login: `admin` / `admin`

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Required. Your OpenAI key |
| `API_KEY` | `dev-key-123` | Bearer key for `/chat` (`X-API-Key` header) |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI chat model |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model |

## Grafana Dashboards

Four auto-provisioned dashboards in the **RAG Chatbot** folder:

| Dashboard   | Key Metric                                           |
| ----------- | ---------------------------------------------------- |
| Latency     | p95/p99 per endpoint, LLM latency, retrieval latency |
| Error Rate  | HTTP 4xx/5xx rate, RAG pipeline errors               |
| Throughput  | Requests per minute, cumulative success count        |
| Token Usage | Avg tokens/request, p95 tokens, token rate, 👍/👎 feedback counts |

<video src="data/readme/Grafana%20dashboard.mov" controls width="100%"></video>

### Generate load for dashboards

```bash
python scripts/load_test.py --n 30
```

![Load test output](data/readme/load-test.png)

## Demo Questions

- "What is Grafana Loki?"
- "How do I create a dashboard in Grafana?"
- "What data sources does Grafana support?"
- "How does Grafana alerting work?"
- "What is the difference between Grafana OSS and Enterprise?"

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Project Structure

```
app/
  main.py           # FastAPI app, Prometheus wiring, lifespan
  config.py         # Pydantic BaseSettings
  auth.py           # X-API-Key middleware (verify_api_key)
  reranker.py       # Cross-encoder reranking (ms-marco-MiniLM-L-6-v2)
  api/
    chat.py         # POST /chat — RAG + metrics + auth
    feedback.py     # POST /feedback — thumbs up/down counter
    health.py       # GET /health
  rag/
    pipeline.py     # Retrieval + reranking + ConversationBufferMemory + timed phases
    embeddings.py   # OpenAI embeddings
    vectorstore.py  # ChromaDB PersistentClient
  metrics/
    custom.py       # Histograms: tokens, retrieval latency, LLM latency; Counter: feedback
frontend/
  gradio_app.py     # Gradio ChatInterface with thumbs up/down feedback
scripts/
  download_docs.py  # Fetch ~60 Grafana .md files from GitHub
  ingest_docs.py    # Chunk + embed into ChromaDB
  load_test.py      # Generate traffic for dashboards
observability/
  prometheus/       # prometheus.yml
  grafana/          # Provisioned datasource + dashboards
```

## Key Design Decisions

- **ChromaDB PersistentClient** (not ephemeral) — survives container restarts via volume mount
- **Timed phases** — retrieval and LLM latency tracked separately for debugging bottlenecks
- **CORS enabled** — Gradio → FastAPI cross-origin calls work out of the box
- **Docker service names** — never `localhost` for cross-container URLs
- **ARM Mac compatible** — Dockerfile includes `build-essential` for HNSWLIB compilation
- **Cross-encoder baked into image** — `ms-marco-MiniLM-L-6-v2` is downloaded at `docker build` time so startup is fast
- **Session memory is in-process** — `ConversationBufferMemory` lives in the FastAPI process dict; it resets on container restart (fine for a portfolio project, swap for Redis in production)
- **Feedback needs no DB** — thumbs up/down go straight to a Prometheus counter; durable storage is a natural next step
