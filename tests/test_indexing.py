from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from openagenda_rag.indexing import (
    INDEXED_DOCUMENT_COLUMNS,
    build_documents,
    build_indexed_documents_frame,
    build_vector_store,
    load_events_for_indexing,
    load_vector_store,
    save_vector_store,
)


def _sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_uid": "evt-1",
                "agenda_uid": "agenda-1",
                "title": "Concert jazz",
                "summary": "Un concert en plein air",
                "long_description": None,
                "text_for_embedding": "Concert jazz en plein air a Paris",
                "city": "Paris",
                "location_name": "Parc floral",
                "latitude": 48.84,
                "longitude": 2.44,
                "first_timing": "2025-06-21T18:00:00Z",
                "last_timing": "2025-06-21T20:00:00Z",
                "timezone": "Europe/Paris",
                "canonical_url": "https://example.com/evt-1",
                "categories": ["music", "outdoor"],
                "source_updated_at": "2025-06-01T12:00:00Z",
                "raw_event": {"uid": "evt-1"},
            },
            {
                "event_uid": "evt-1",
                "agenda_uid": "agenda-1",
                "title": "Concert jazz duplicate",
                "summary": "Doublon",
                "long_description": None,
                "text_for_embedding": "Concert jazz en plein air a Paris",
                "city": "Paris",
                "location_name": "Parc floral",
                "latitude": 48.84,
                "longitude": 2.44,
                "first_timing": "2025-06-21T18:00:00Z",
                "last_timing": "2025-06-21T20:00:00Z",
                "timezone": "Europe/Paris",
                "canonical_url": "https://example.com/evt-1",
                "categories": ["music", "outdoor"],
                "source_updated_at": "2025-06-01T12:00:00Z",
                "raw_event": {"uid": "evt-1"},
            },
            {
                "event_uid": "evt-2",
                "agenda_uid": "agenda-1",
                "title": "Description vide",
                "summary": None,
                "long_description": None,
                "text_for_embedding": "   ",
                "city": "Paris",
                "location_name": "Mairie",
                "latitude": None,
                "longitude": None,
                "first_timing": "2025-06-22T10:00:00Z",
                "last_timing": "2025-06-22T12:00:00Z",
                "timezone": "Europe/Paris",
                "canonical_url": "https://example.com/evt-2",
                "categories": [],
                "source_updated_at": "2025-06-02T12:00:00Z",
                "raw_event": {"uid": "evt-2"},
            },
        ]
    )


class FakeDocument:
    def __init__(self, page_content: str, metadata: dict):
        self.page_content = page_content
        self.metadata = metadata


class FakeTextSplitter:
    def __init__(self, chunk_size: int, chunk_overlap: int, add_start_index: bool = False):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.add_start_index = add_start_index

    def split_documents(self, documents):
        split_documents = []
        step = max(1, self.chunk_size - self.chunk_overlap)
        for document in documents:
            text = document.page_content
            if not text:
                split_documents.append(FakeDocument(text, dict(document.metadata)))
                continue
            start = 0
            while start < len(text):
                chunk = text[start : start + self.chunk_size]
                metadata = dict(document.metadata)
                if self.add_start_index:
                    metadata["start_index"] = start
                split_documents.append(FakeDocument(chunk, metadata))
                start += step
        return split_documents


class FakeEmbeddings:
    def __init__(self, model: str, api_key: str | None = None, mistral_api_key: str | None = None):
        self.model = model
        self.api_key = api_key or mistral_api_key


class FakeFAISS:
    def __init__(self, documents, embedding):
        self.documents = list(documents)
        self.embedding = embedding

    @classmethod
    def from_documents(cls, documents, embedding):
        return cls(documents, embedding)

    def add_documents(self, documents):
        self.documents.extend(documents)

    def save_local(self, folder_path: str):
        path = Path(folder_path)
        path.mkdir(parents=True, exist_ok=True)
        payload = [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in self.documents]
        (path / "fake_index.json").write_text(json.dumps(payload, ensure_ascii=True))

    @classmethod
    def load_local(cls, folder_path: str, embeddings, allow_dangerous_deserialization: bool = False):
        path = Path(folder_path)
        payload = json.loads((path / "fake_index.json").read_text())
        documents = [FakeDocument(item["page_content"], item["metadata"]) for item in payload]
        return cls(documents, embeddings)

    def similarity_search(self, query: str, k: int = 4):
        matches = [
            doc
            for doc in self.documents
            if any(token in doc.page_content.lower() for token in query.lower().split())
        ]
        return matches[:k]


def test_load_events_for_indexing_filters_empty_text_and_duplicate_events(tmp_path: Path):
    input_path = tmp_path / "events.parquet"
    _sample_frame().to_parquet(input_path, index=False)

    frame = load_events_for_indexing(input_path)

    assert frame["event_uid"].tolist() == ["evt-1"]
    assert frame.iloc[0]["title"] == "Concert jazz"


def test_load_events_for_indexing_requires_source_dataset(tmp_path: Path):
    missing_path = tmp_path / "missing.parquet"

    with pytest.raises(FileNotFoundError) as exc:
        load_events_for_indexing(missing_path)

    assert "fetch_events.py" in str(exc.value)


def test_build_documents_preserves_page_content_and_metadata(monkeypatch):
    from openagenda_rag import indexing

    monkeypatch.setattr(indexing, "_get_document_class", lambda: FakeDocument)
    monkeypatch.setattr(indexing, "_get_text_splitter_class", lambda: FakeTextSplitter)
    frame = _sample_frame().iloc[[0]].copy()

    documents = build_documents(frame, chunk_size=100, chunk_overlap=0)

    assert len(documents) == 1
    assert documents[0].page_content == "Concert jazz en plein air a Paris"
    assert documents[0].metadata["event_uid"] == "evt-1"
    assert documents[0].metadata["chunk_id"] == "evt-1::chunk-0"
    assert documents[0].metadata["chunk_index"] == 0
    assert documents[0].metadata["chunk_start"] == 0
    assert documents[0].metadata["categories"] == ["music", "outdoor"]
    assert set(documents[0].metadata) == {
        "chunk_id",
        "chunk_index",
        "chunk_start",
        "event_uid",
        "agenda_uid",
        "title",
        "city",
        "location_name",
        "first_timing",
        "last_timing",
        "timezone",
        "canonical_url",
        "categories",
        "source_updated_at",
    }


def test_build_documents_splits_long_event_text_into_multiple_chunks(monkeypatch):
    from openagenda_rag import indexing

    monkeypatch.setattr(indexing, "_get_document_class", lambda: FakeDocument)
    monkeypatch.setattr(indexing, "_get_text_splitter_class", lambda: FakeTextSplitter)
    frame = _sample_frame().iloc[[0]].copy()
    frame.loc[frame.index[0], "text_for_embedding"] = "abcdefghij" * 6

    documents = build_documents(frame, chunk_size=20, chunk_overlap=5)

    assert len(documents) > 1
    assert [doc.metadata["chunk_index"] for doc in documents] == list(range(len(documents)))
    assert documents[0].metadata["event_uid"] == "evt-1"
    assert documents[1].metadata["chunk_start"] == 15


def test_build_vector_store_and_load_vector_store_roundtrip(monkeypatch, tmp_path: Path):
    from openagenda_rag import indexing

    monkeypatch.setattr(indexing, "_get_document_class", lambda: FakeDocument)
    monkeypatch.setattr(indexing, "_get_text_splitter_class", lambda: FakeTextSplitter)
    monkeypatch.setattr(indexing, "_get_faiss_class", lambda: FakeFAISS)
    monkeypatch.setattr(indexing, "_get_mistral_embeddings_class", lambda: FakeEmbeddings)
    frame = _sample_frame().iloc[[0]].copy()
    documents = build_documents(frame, chunk_size=100, chunk_overlap=0)

    vector_store = build_vector_store(
        documents=documents,
        embedding_model="mistral-embed",
        api_key="test-key",
        batch_size=1,
    )
    manifest = {"indexed_event_count": 1, "embedding_model": "mistral-embed"}
    output_dir = tmp_path / "faiss"
    save_vector_store(vector_store, output_dir, manifest)

    loaded_store = load_vector_store(
        output_dir=output_dir,
        embedding_model="mistral-embed",
        api_key="test-key",
    )
    matches = loaded_store.similarity_search("jazz", k=1)

    assert matches[0].metadata["event_uid"] == "evt-1"
    assert (output_dir / "fake_index.json").exists()
    assert (output_dir.parent / "index_manifest.json").exists()


def test_build_indexed_documents_frame_tracks_chunk_metadata(monkeypatch):
    from openagenda_rag import indexing

    monkeypatch.setattr(indexing, "_get_document_class", lambda: FakeDocument)
    monkeypatch.setattr(indexing, "_get_text_splitter_class", lambda: FakeTextSplitter)
    frame = _sample_frame().iloc[[0]].copy()
    frame.loc[frame.index[0], "text_for_embedding"] = "abcdefghij" * 6

    documents = build_documents(frame, chunk_size=20, chunk_overlap=5)
    indexed_frame = build_indexed_documents_frame(documents)

    assert "raw_event" not in indexed_frame.columns
    assert "chunk_id" in indexed_frame.columns
    assert indexed_frame.iloc[0]["event_uid"] == "evt-1"
    assert indexed_frame.iloc[1]["chunk_index"] == 1
    assert indexed_frame.columns.tolist().count("text_for_embedding") == 1


def test_indexed_document_columns_exclude_raw_payload():
    assert "raw_event" not in INDEXED_DOCUMENT_COLUMNS
    assert "event_uid" in INDEXED_DOCUMENT_COLUMNS
    assert "chunk_id" in INDEXED_DOCUMENT_COLUMNS
