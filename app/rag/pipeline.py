import time
from typing import Any

from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.config import settings
from app.rag.vectorstore import get_vectorstore
from app.reranker import rerank_documents

PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpful assistant that answers questions about Grafana "
        "based on the provided documentation context.\n\n"
        "Context:\n{context}\n\n"
        "Answer concisely and accurately. If the context does not contain "
        "enough information, say so.",
    ),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])

# In-memory store: session_id -> ConversationBufferMemory
_session_memories: dict[str, ConversationBufferMemory] = {}


def _get_memory(session_id: str) -> ConversationBufferMemory:
    if session_id not in _session_memories:
        _session_memories[session_id] = ConversationBufferMemory(
            return_messages=True, memory_key="history"
        )
    return _session_memories[session_id]


def _format_docs(docs: list) -> str:
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


class RAGPipeline:
    def __init__(self) -> None:
        self.vectorstore = get_vectorstore()
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity", search_kwargs={"k": 6}
        )
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            openai_api_key=settings.openai_api_key,
            temperature=0,
        )

    def query(self, question: str, session_id: str = "default") -> dict[str, Any]:
        memory = _get_memory(session_id)

        # Time retrieval + reranking phase
        t0 = time.perf_counter()
        docs = self.retriever.invoke(question)
        docs = rerank_documents(question, docs, top_k=3)
        retrieval_latency = time.perf_counter() - t0

        context = _format_docs(docs)
        history = memory.chat_memory.messages

        # Time LLM phase
        prompt = PROMPT_TEMPLATE.format_messages(
            context=context, question=question, history=history
        )
        t1 = time.perf_counter()
        response = self.llm.invoke(prompt)
        llm_latency = time.perf_counter() - t1

        # Persist exchange to memory
        memory.chat_memory.add_user_message(question)
        memory.chat_memory.add_ai_message(response.content)

        tokens_used = 0
        try:
            tokens_used = response.usage_metadata.get("total_tokens", 0)
        except (AttributeError, TypeError):
            try:
                tokens_used = response.response_metadata["token_usage"]["total_tokens"]
            except (KeyError, TypeError):
                tokens_used = 0

        sources = list({doc.metadata.get("source", "") for doc in docs if doc.metadata.get("source")})

        return {
            "answer": response.content,
            "sources": sources,
            "tokens_used": tokens_used,
            "retrieval_latency": retrieval_latency,
            "llm_latency": llm_latency,
        }

    def doc_count(self) -> int:
        try:
            return self.vectorstore._collection.count()
        except Exception:
            return 0
