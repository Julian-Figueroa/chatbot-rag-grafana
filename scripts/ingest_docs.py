"""
One-time script: load Grafana docs from data/docs/, chunk, embed, upsert into ChromaDB.
Run from project root: python scripts/ingest_docs.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from app.config import settings
from app.rag.embeddings import get_embeddings


def ingest() -> None:
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "docs")
    if not os.path.exists(docs_dir) or not os.listdir(docs_dir):
        print(f"ERROR: No docs found in {docs_dir}. Run scripts/download_docs.py first.")
        sys.exit(1)

    print(f"Loading docs from {docs_dir}...")
    loader = DirectoryLoader(
        docs_dir,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    raw_docs = loader.load()
    print(f"Loaded {len(raw_docs)} files.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(raw_docs)
    print(f"Split into {len(chunks)} chunks.")

    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    vectorstore = Chroma(
        client=client,
        collection_name=settings.chroma_collection_name,
        embedding_function=get_embeddings(),
    )

    print("Embedding and upserting into ChromaDB (this may take a minute)...")
    vectorstore.add_documents(chunks)

    count = vectorstore._collection.count()
    print(f"Done. ChromaDB collection '{settings.chroma_collection_name}' now has {count} documents.")


if __name__ == "__main__":
    ingest()
