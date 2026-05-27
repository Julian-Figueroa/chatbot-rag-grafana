import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api import chat, health
from app.api import feedback
from app.rag.pipeline import RAGPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing RAG pipeline...")
    pipeline = RAGPipeline()
    doc_count = pipeline.doc_count()
    if doc_count == 0:
        logger.warning(
            "ChromaDB collection is EMPTY. Run scripts/ingest_docs.py before querying."
        )
    else:
        logger.info(f"ChromaDB ready: {doc_count} documents indexed.")
    app.state.pipeline = pipeline
    yield
    logger.info("Shutting down.")


app = FastAPI(title="Grafana RAG Chatbot", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

app.include_router(chat.router)
app.include_router(health.router)
app.include_router(feedback.router)
