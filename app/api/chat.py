from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.auth import verify_api_key
from app.metrics.custom import (
    rag_llm_latency_seconds,
    rag_requests_total,
    rag_retrieval_latency_seconds,
    rag_tokens_per_request,
)

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    tokens_used: int


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    pipeline = request.app.state.pipeline
    try:
        result = pipeline.query(body.question, session_id=body.session_id)
    except Exception as exc:
        rag_requests_total.labels(status="error").inc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    rag_tokens_per_request.observe(result["tokens_used"])
    rag_retrieval_latency_seconds.observe(result["retrieval_latency"])
    rag_llm_latency_seconds.observe(result["llm_latency"])
    rag_requests_total.labels(status="success").inc()

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        tokens_used=result["tokens_used"],
    )
