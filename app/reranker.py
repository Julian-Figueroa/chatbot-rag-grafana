from sentence_transformers import CrossEncoder

# Load once at the start (FAstAPI lifespan)
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank_documents(query: str, docs: list, top_k: int = 3) -> list:
  pairs = [(query, doc.page_content) for doc in docs]
  scores = cross_encoder.predict(pairs)
  scored_docs = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
  return [doc for doc, _ in scored_docs[:top_k]]