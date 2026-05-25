import time
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from app.config import settings
from app.rag.vectorstore import get_vectorstore

PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpful assistant that answers questions about Grafana "
        "based on the provided documentation context.\n\n"
        "Context:\n{context}\n\n"
        "Answer concisely and accurately. If the context does not contain "
        "enough information, say so.",
    ),
    ("human", "{question}"),
])


def _format_docs(docs: list) -> str:
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


class RAGPipeline:
    def __init__(self) -> None:
        self.vectorstore = get_vectorstore()
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity", search_kwargs={"k": 4}
        )
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            openai_api_key=settings.openai_api_key,
            temperature=0,
        )
        self._chain = (
            {"context": self.retriever | _format_docs, "question": RunnablePassthrough()}
            | PROMPT_TEMPLATE
            | self.llm
            | StrOutputParser()
        )

    def query(self, question: str) -> dict[str, Any]:
        # Time retrieval phase
        t0 = time.perf_counter()
        docs = self.retriever.invoke(question)
        retrieval_latency = time.perf_counter() - t0

        # Time LLM phase
        context = _format_docs(docs)
        prompt = PROMPT_TEMPLATE.format_messages(context=context, question=question)
        t1 = time.perf_counter()
        response = self.llm.invoke(prompt)
        llm_latency = time.perf_counter() - t1

        answer = response.content

        # Extract token usage
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
            "answer": answer,
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
