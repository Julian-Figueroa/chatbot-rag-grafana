import pytest
from unittest.mock import patch
from fastapi import HTTPException
from langchain_core.documents import Document


# --- reranker ---

def test_rerank_orders_by_score():
    docs = [
        Document(page_content="doc A"),
        Document(page_content="doc B"),
        Document(page_content="doc C"),
    ]
    with patch("app.reranker.cross_encoder") as mock_ce:
        mock_ce.predict.return_value = [0.1, 0.9, 0.5]
        from app.reranker import rerank_documents
        result = rerank_documents("query", docs, top_k=2)

    assert result[0].page_content == "doc B"
    assert result[1].page_content == "doc C"
    assert len(result) == 2


def test_rerank_respects_top_k():
    docs = [Document(page_content=f"doc {i}") for i in range(5)]
    with patch("app.reranker.cross_encoder") as mock_ce:
        mock_ce.predict.return_value = [0.5, 0.4, 0.3, 0.2, 0.1]
        from app.reranker import rerank_documents
        result = rerank_documents("query", docs, top_k=3)

    assert len(result) == 3


def test_rerank_calls_predict_with_pairs():
    docs = [Document(page_content="alpha"), Document(page_content="beta")]
    with patch("app.reranker.cross_encoder") as mock_ce:
        mock_ce.predict.return_value = [0.8, 0.2]
        from app.reranker import rerank_documents
        rerank_documents("my query", docs)

    mock_ce.predict.assert_called_once_with([("my query", "alpha"), ("my query", "beta")])


# --- verify_api_key ---

def test_verify_api_key_valid(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret-key")
    from app.auth import verify_api_key
    verify_api_key("secret-key")  # should not raise


def test_verify_api_key_wrong_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret-key")
    from app.auth import verify_api_key
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key("wrong-key")
    assert exc_info.value.status_code == 403


def test_verify_api_key_empty(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret-key")
    from app.auth import verify_api_key
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key("")
    assert exc_info.value.status_code == 403
