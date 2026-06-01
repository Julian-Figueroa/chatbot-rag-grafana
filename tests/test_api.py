"""
Smoke tests for the FastAPI backend.
Requires a running backend at BACKEND_URL (default http://localhost:8000)
or uses TestClient with mocked pipeline for unit tests.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_pipeline():
    pipeline = MagicMock()
    pipeline.doc_count.return_value = 42
    pipeline.query.return_value = {
        "answer": "Grafana Loki is a log aggregation system.",
        "sources": ["datasources_loki.md"],
        "tokens_used": 150,
        "retrieval_latency": 0.05,
        "llm_latency": 1.2,
    }
    return pipeline


@pytest.fixture
def client(mock_pipeline, monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    with patch("app.main.RAGPipeline", return_value=mock_pipeline):
        from app.main import app
        with TestClient(app) as c:
            yield c


def test_health(client, mock_pipeline):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["chroma_doc_count"] == 42


def test_chat(client, mock_pipeline):
    response = client.post(
        "/chat",
        json={"question": "What is Grafana Loki?"},
        headers={"X-API-Key": "test-key"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "tokens_used" in data
    assert len(data["answer"]) > 0
    mock_pipeline.query.assert_called_once_with("What is Grafana Loki?", session_id="default")


def test_chat_requires_api_key(client):
    response = client.post("/chat", json={"question": "What is Grafana Loki?"})
    assert response.status_code == 403


def test_chat_wrong_api_key(client):
    response = client.post(
        "/chat",
        json={"question": "What is Grafana Loki?"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 403


def test_chat_missing_question(client):
    response = client.post("/chat", json={}, headers={"X-API-Key": "test-key"})
    assert response.status_code == 422


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"http_requests_total" in response.content or b"rag_" in response.content
