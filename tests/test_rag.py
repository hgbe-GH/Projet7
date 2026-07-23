from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from openagenda_rag.rag import (
    answer_question,
    build_retriever,
    build_source_entries,
    format_documents_for_prompt,
)
from openagenda_rag.service import OpenAgendaRAGService


@dataclass
class FakeDocument:
    page_content: str
    metadata: dict


class FakeRetriever:
    def __init__(self, documents):
        self.documents = list(documents)
        self.queries = []

    def invoke(self, question: str):
        self.queries.append(question)
        return list(self.documents)


class FakeChatResponse:
    def __init__(self, content: str):
        self.content = content


class FakeChatModel:
    def __init__(self, content: str = "Voici une recommandation."):
        self.content = content
        self.messages = []

    def invoke(self, messages):
        self.messages.append(messages)
        return FakeChatResponse(self.content)


class FakeVectorStore:
    def __init__(self):
        self.calls = []

    def as_retriever(self, search_type: str = "similarity", search_kwargs: dict | None = None):
        self.calls.append({"search_type": search_type, "search_kwargs": search_kwargs})
        return FakeRetriever([])


def _sample_documents():
    return [
        FakeDocument(
            page_content="Concert jazz en plein air a Paris.",
            metadata={
                "event_uid": "evt-1",
                "chunk_id": "evt-1::chunk-0",
                "title": "Concert jazz",
                "city": "Paris",
                "location_name": "Parc floral",
                "first_timing": "2025-06-21T18:00:00Z",
                "last_timing": "2025-06-21T20:00:00Z",
                "canonical_url": "https://example.com/evt-1",
                "categories": ["music", "outdoor"],
            },
        ),
        FakeDocument(
            page_content="Deuxieme chunk du meme evenement.",
            metadata={
                "event_uid": "evt-1",
                "chunk_id": "evt-1::chunk-1",
                "title": "Concert jazz",
                "city": "Paris",
                "location_name": "Parc floral",
                "first_timing": "2025-06-21T18:00:00Z",
                "last_timing": "2025-06-21T20:00:00Z",
                "canonical_url": "https://example.com/evt-1",
                "categories": ["music", "outdoor"],
            },
        ),
        FakeDocument(
            page_content="Exposition photo a Lyon.",
            metadata={
                "event_uid": "evt-2",
                "chunk_id": "evt-2::chunk-0",
                "title": "Expo photo",
                "city": "Lyon",
                "location_name": "Musee",
                "first_timing": "2025-06-22T10:00:00Z",
                "last_timing": "2025-06-22T18:00:00Z",
                "canonical_url": "https://example.com/evt-2",
                "categories": ["photo"],
            },
        ),
    ]


def test_build_source_entries_deduplicates_same_event():
    sources = build_source_entries(_sample_documents())

    assert len(sources) == 2
    assert sources[0].event_uid == "evt-1"
    assert sources[1].event_uid == "evt-2"


def test_build_source_entries_normalizes_stringified_categories():
    sources = build_source_entries(
        [
            FakeDocument(
                page_content="Concert",
                metadata={
                    "event_uid": "evt-1",
                    "chunk_id": "evt-1::chunk-0",
                    "title": "Concert jazz",
                    "city": "Paris",
                    "location_name": "Parc floral",
                    "first_timing": "2025-06-21T18:00:00Z",
                    "last_timing": "2025-06-21T20:00:00Z",
                    "canonical_url": "https://example.com/evt-1",
                    "categories": "['music' 'outdoor']",
                },
            )
        ]
    )

    assert sources[0].categories == ["music", "outdoor"]


def test_build_source_entries_normalizes_list_wrapped_stringified_categories():
    sources = build_source_entries(
        [
            FakeDocument(
                page_content="Concert",
                metadata={
                    "event_uid": "evt-1",
                    "chunk_id": "evt-1::chunk-0",
                    "title": "Concert jazz",
                    "city": "Paris",
                    "location_name": "Parc floral",
                    "first_timing": "2025-06-21T18:00:00Z",
                    "last_timing": "2025-06-21T20:00:00Z",
                    "canonical_url": "https://example.com/evt-1",
                    "categories": ["['music' 'outdoor']"],
                },
            )
        ]
    )

    assert sources[0].categories == ["music", "outdoor"]


def test_format_documents_for_prompt_includes_metadata_and_content():
    prompt_context = format_documents_for_prompt(_sample_documents()[:1])

    assert "Titre: Concert jazz" in prompt_context
    assert "Ville: Paris" in prompt_context
    assert "Concert jazz en plein air a Paris." in prompt_context
    assert "https://example.com/evt-1" in prompt_context


def test_answer_question_returns_answer_sources_and_chunk_count():
    retriever = FakeRetriever(_sample_documents())
    chat_model = FakeChatModel("Je recommande le concert jazz a Paris.")

    payload = answer_question(
        question="Je cherche un concert a Paris",
        retriever=retriever,
        chat_model=chat_model,
    )

    assert payload["question"] == "Je cherche un concert a Paris"
    assert payload["answer"] == "Je recommande le concert jazz a Paris."
    assert payload["retrieved_chunk_count"] == 3
    assert "retrieved_contexts" not in payload
    assert len(payload["sources"]) == 2
    assert retriever.queries == ["Je cherche un concert a Paris"]
    assert chat_model.messages


def test_answer_question_includes_non_empty_retrieved_contexts_in_order_when_requested():
    documents = _sample_documents()
    documents.insert(1, FakeDocument(page_content="", metadata={}))
    retriever = FakeRetriever(documents)
    chat_model = FakeChatModel()

    payload = answer_question(
        question="Je cherche un evenement",
        retriever=retriever,
        chat_model=chat_model,
        include_contexts=True,
    )

    assert len(payload["retrieved_contexts"]) == 3
    assert "Titre: Concert jazz" in payload["retrieved_contexts"][0]
    assert "URL: https://example.com/evt-1" in payload["retrieved_contexts"][0]
    assert "Concert jazz en plein air a Paris." in payload["retrieved_contexts"][0]
    assert "Deuxieme chunk du meme evenement." in payload["retrieved_contexts"][1]
    assert "Exposition photo a Lyon." in payload["retrieved_contexts"][2]


def test_answer_question_returns_fallback_when_no_document_is_found():
    retriever = FakeRetriever([])
    chat_model = FakeChatModel("unused")

    payload = answer_question(
        question="Quel evenement sur Mars ?",
        retriever=retriever,
        chat_model=chat_model,
    )

    assert "Je ne sais pas" in payload["answer"]
    assert payload["sources"] == []
    assert payload["retrieved_chunk_count"] == 0
    assert "retrieved_contexts" not in payload
    assert chat_model.messages == []


def test_answer_question_includes_empty_retrieved_contexts_when_no_document_is_found():
    payload = answer_question(
        question="Quel evenement sur Mars ?",
        retriever=FakeRetriever([]),
        chat_model=FakeChatModel("unused"),
        include_contexts=True,
    )

    assert payload["retrieved_contexts"] == []


def test_service_ask_for_evaluation_requests_retrieved_contexts(monkeypatch):
    service = object.__new__(OpenAgendaRAGService)
    retriever = FakeRetriever([])
    chat_model = FakeChatModel()
    service._ensure_runtime = lambda: (retriever, chat_model)
    calls = []

    def fake_answer_question(**kwargs):
        calls.append(kwargs)
        return {"retrieved_contexts": []}

    monkeypatch.setattr("openagenda_rag.service.answer_question", fake_answer_question)

    payload = service.ask_for_evaluation("Quel evenement ?")

    assert payload == {"retrieved_contexts": []}
    assert calls == [
        {
            "question": "Quel evenement ?",
            "retriever": retriever,
            "chat_model": chat_model,
            "include_contexts": True,
        }
    ]


def test_build_retriever_uses_similarity_search_kwargs(monkeypatch):
    from openagenda_rag import rag

    fake_vector_store = FakeVectorStore()
    monkeypatch.setattr(rag, "load_vector_store", lambda *args, **kwargs: fake_vector_store)

    build_retriever(
        index_output_dir=Path("data/index/faiss"),
        embedding_model="mistral-embed",
        api_key="test-key",
        top_k=6,
    )

    assert fake_vector_store.calls == [{"search_type": "similarity", "search_kwargs": {"k": 6}}]
