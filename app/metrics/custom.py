from prometheus_client import Counter, Histogram

rag_tokens_per_request = Histogram(
    "rag_tokens_per_request",
    "Total tokens used per RAG request",
    buckets=[50, 100, 200, 500, 1000, 2000, 5000],
)

rag_retrieval_latency_seconds = Histogram(
    "rag_retrieval_latency_seconds",
    "Latency of the ChromaDB retrieval step",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)

rag_llm_latency_seconds = Histogram(
    "rag_llm_latency_seconds",
    "Latency of the LLM completion step",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0],
)

rag_requests_total = Counter(
    "rag_requests_total",
    "Total number of RAG /chat requests",
    ["status"],
)
