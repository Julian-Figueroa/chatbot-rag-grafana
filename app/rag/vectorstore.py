import chromadb
from langchain_chroma import Chroma
from app.config import settings
from app.rag.embeddings import get_embeddings


def get_vectorstore() -> Chroma:
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return Chroma(
        client=client,
        collection_name=settings.chroma_collection_name,
        embedding_function=get_embeddings(),
    )
