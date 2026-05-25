from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict:
    pipeline = request.app.state.pipeline
    doc_count = pipeline.doc_count()
    return {"status": "ok", "chroma_doc_count": doc_count}
