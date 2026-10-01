from __future__ import annotations

from fastapi.testclient import TestClient
import httpx
import pytest

from openagenda_rag.api import create_app


class FakeService:
    def __init__(self):
        self.ask_calls = []
        self.rebuild_calls = []

    def health(self):
        return {
            "status": "ok",
            "index_dir": "/tmp/faiss",
            "chat_model": "mistral-small-latest",
            "embedding_model": "mistral-embed",
            "top_k": 4,
        }

    def ask(self, question: str):
        self.ask_calls.append(question)
        return {
            "question": question,
            "answer": "Reponse de test",
            "sources": [
                {
                    "event_uid": "evt-1",
                    "chunk_id": "evt-1::chunk-0",
                    "title": "Concert jazz",
                    "city": "Paris",
                    "location_name": "Parc floral",
                    "first_timing": "2025-06-21T18:00:00Z",
                    "last_timing": "2025-06-21T20:00:00Z",
                    "canonical_url": "https://example.com/evt-1",
                    "categories": ["music"],
                }
            ],
            "retrieved_chunk_count": 1,
            "retrieved_contexts": ["Contexte brut interne"],
        }

    def rebuild(self, **kwargs):
        self.rebuild_calls.append(kwargs)
        return {
            "manifest_path": "/tmp/index_manifest.json",
            "indexed_documents_path": "/tmp/indexed_documents.parquet",
            "indexed_event_count": 10,
            "indexed_document_count": 12,
            "output_dir": "/tmp/faiss",
            "manifest": {"indexed_document_count": 12},
        }


def test_health_endpoint_returns_service_status():
    app = create_app(service=FakeService())
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ask_endpoint_returns_answer_payload():
    service = FakeService()
    app = create_app(service=service)
    client = TestClient(app)

    response = client.post("/ask", json={"question": "Je cherche un concert"})

    assert response.status_code == 200
    assert response.json() == {
        "question": "Je cherche un concert",
        "answer": "Reponse de test",
        "sources": [
            {
                "event_uid": "evt-1",
                "chunk_id": "evt-1::chunk-0",
                "title": "Concert jazz",
                "city": "Paris",
                "location_name": "Parc floral",
                "first_timing": "2025-06-21T18:00:00Z",
                "last_timing": "2025-06-21T20:00:00Z",
                "canonical_url": "https://example.com/evt-1",
                "categories": ["music"],
            }
        ],
        "retrieved_chunk_count": 1,
    }
    assert "retrieved_contexts" not in response.json()
    assert service.ask_calls == ["Je cherche un concert"]


def test_ask_endpoint_rejects_blank_question():
    app = create_app(service=FakeService())
    client = TestClient(app)

    response = client.post("/ask", json={"question": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "Question must not be empty."


def test_rebuild_endpoint_executes_service_rebuild():
    service = FakeService()
    app = create_app(service=service)
    client = TestClient(app)

    response = client.post("/rebuild", json={"chunk_size": 2000, "chunk_overlap": 100})

    assert response.status_code == 200
    assert response.json()["indexed_document_count"] == 12
    assert service.rebuild_calls == [{"batch_size": None, "chunk_size": 2000, "chunk_overlap": 100, "embedding_model": None}]


def test_rebuild_endpoint_rejects_invalid_overlap():
    app = create_app(service=FakeService())
    client = TestClient(app)

    response = client.post("/rebuild", json={"chunk_size": 500, "chunk_overlap": 500})

    assert response.status_code == 400
    assert response.json()["detail"] == "chunk_overlap must be smaller than chunk_size."


def test_rebuild_endpoint_checks_admin_token_when_configured():
    app = create_app(service=FakeService())
    app.state.api_settings.rebuild_token = "secret"
    client = TestClient(app)

    response = client.post("/rebuild", json={})

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid admin token."


@pytest.mark.parametrize("endpoint", ["/ask", "/rebuild"])
@pytest.mark.parametrize("upstream_status, expected_status", [(429, 503), (401, 503), (502, 502)])
def test_provider_http_errors_are_controlled_without_leaking_details(endpoint, upstream_status, expected_status):
    request = httpx.Request("POST", "https://api.mistral.ai/v1/chat/completions")
    upstream = httpx.Response(upstream_status, request=request, json={"secret": "private-detail"})

    class UnavailableService(FakeService):
        def ask(self, question):
            raise httpx.HTTPStatusError("private-detail", request=request, response=upstream)

        def rebuild(self, **kwargs):
            return self.ask("")

    client = TestClient(create_app(service=UnavailableService()))
    response = client.post(endpoint, json={"question": "Concert"} if endpoint == "/ask" else {})

    assert response.status_code == expected_status
    assert "private-detail" not in response.text
    assert "Mistral" in response.json()["detail"]
    if upstream_status == 429:
        assert "429" in response.json()["detail"]


@pytest.mark.parametrize("endpoint", ["/ask", "/rebuild"])
def test_provider_timeout_is_reported_as_unavailable(endpoint):
    class TimeoutService(FakeService):
        def ask(self, question):
            raise httpx.ReadTimeout("private-detail")

        def rebuild(self, **kwargs):
            return self.ask("")

    client = TestClient(create_app(service=TimeoutService()))
    response = client.post(endpoint, json={"question": "Concert"} if endpoint == "/ask" else {})
    assert response.status_code == 503
    assert "private-detail" not in response.text


@pytest.mark.parametrize("endpoint", ["/ask", "/rebuild"])
def test_unexpected_errors_do_not_leak_internal_details(endpoint):
    class BrokenService(FakeService):
        def ask(self, question):
            raise RuntimeError("private-detail")

        def rebuild(self, **kwargs):
            return self.ask("")

    client = TestClient(create_app(service=BrokenService()))
    response = client.post(endpoint, json={"question": "Concert"} if endpoint == "/ask" else {})
    assert response.status_code == 500
    assert "private-detail" not in response.text
