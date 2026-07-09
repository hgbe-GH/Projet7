from __future__ import annotations

from pathlib import Path
import json
import os
import shutil
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from langchain_core.documents import Document
    from langchain_community.vectorstores import FAISS


REQUIRED_INDEX_COLUMNS = [
    "event_uid",
    "text_for_embedding",
    "title",
    "city",
    "first_timing",
    "canonical_url",
    "categories",
]

DOCUMENT_METADATA_COLUMNS = [
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
]

INDEXED_DOCUMENT_COLUMNS = [
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
    "text_for_embedding",
]

MANIFEST_FILENAME = "index_manifest.json"
INDEXED_DOCUMENTS_FILENAME = "indexed_documents.parquet"


def _get_document_class():
    from langchain_core.documents import Document

    return Document


def _get_faiss_class():
    from langchain_community.vectorstores import FAISS

    return FAISS


def _get_mistral_embeddings_class():
    from langchain_mistralai import MistralAIEmbeddings

    return MistralAIEmbeddings


def _get_text_splitter_class():
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    return RecursiveCharacterTextSplitter


def _normalize_categories(value: Any) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    return [str(value)]


def _normalize_scalar(value: Any) -> Any:
    if value is None:
        return None
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _sanitize_chunk_size(chunk_size: int) -> int:
    return max(1, int(chunk_size))


def _sanitize_chunk_overlap(chunk_size: int, chunk_overlap: int) -> int:
    return max(0, min(int(chunk_overlap), _sanitize_chunk_size(chunk_size) - 1))


def _build_embeddings(embedding_model: str, api_key: str):
    if not api_key:
        raise ValueError("A Mistral API key is required to build or load the FAISS index.")

    os.environ.setdefault("MISTRAL_API_KEY", api_key)
    os.environ.setdefault("MISTRALAI_API_KEY", api_key)
    embeddings_class = _get_mistral_embeddings_class()

    try:
        return embeddings_class(model=embedding_model, api_key=api_key)
    except TypeError:
        try:
            return embeddings_class(model=embedding_model, mistral_api_key=api_key)
        except TypeError:
            return embeddings_class(model=embedding_model)


def load_events_for_indexing(input_path: Path) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(
            f"Normalized dataset not found at {input_path}. Run scripts/fetch_events.py first."
        )

    frame = pd.read_parquet(input_path)
    missing_columns = [column for column in REQUIRED_INDEX_COLUMNS if column not in frame.columns]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Input dataset is missing required columns: {missing}")

    if "event_uid" in frame.columns:
        frame = frame.drop_duplicates(subset=["event_uid"], keep="first")

    text_series = frame["text_for_embedding"].fillna("").astype(str).str.strip()
    frame = frame.loc[text_series != ""].copy()
    frame["text_for_embedding"] = text_series.loc[frame.index]
    return frame


def build_documents(
    frame: pd.DataFrame,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list["Document"]:
    document_class = _get_document_class()
    splitter_class = _get_text_splitter_class()
    effective_chunk_size = _sanitize_chunk_size(chunk_size)
    effective_chunk_overlap = _sanitize_chunk_overlap(effective_chunk_size, chunk_overlap)
    splitter = splitter_class(
        chunk_size=effective_chunk_size,
        chunk_overlap=effective_chunk_overlap,
        add_start_index=True,
    )

    base_documents = []
    for row in frame.to_dict(orient="records"):
        metadata = {
            key: _normalize_categories(value) if key == "categories" else _normalize_scalar(value)
            for key, value in row.items()
            if key in DOCUMENT_METADATA_COLUMNS
        }
        base_documents.append(
            document_class(
                page_content=str(row["text_for_embedding"]).strip(),
                metadata=metadata,
            )
        )

    split_documents = splitter.split_documents(base_documents)
    chunk_counters: dict[str, int] = {}
    documents: list["Document"] = []
    for doc in split_documents:
        event_uid = str(doc.metadata["event_uid"])
        chunk_index = chunk_counters.get(event_uid, 0)
        metadata = dict(doc.metadata)
        metadata["chunk_id"] = f"{event_uid}::chunk-{chunk_index}"
        metadata["chunk_index"] = chunk_index
        metadata["chunk_start"] = metadata.get("start_index")
        metadata.pop("start_index", None)
        documents.append(
            document_class(
                page_content=doc.page_content,
                metadata=metadata,
            )
        )
        chunk_counters[event_uid] = chunk_index + 1

    return documents


def build_vector_store(
    documents: list["Document"],
    embedding_model: str,
    api_key: str,
    batch_size: int = 50,
) -> "FAISS":
    if not documents:
        raise ValueError("At least one document is required to build the FAISS index.")

    embeddings = _build_embeddings(embedding_model=embedding_model, api_key=api_key)
    faiss_class = _get_faiss_class()
    effective_batch_size = max(1, batch_size)

    vector_store = faiss_class.from_documents(documents[:effective_batch_size], embeddings)
    for start in range(effective_batch_size, len(documents), effective_batch_size):
        vector_store.add_documents(documents[start : start + effective_batch_size])

    return vector_store


def save_vector_store(vector_store: "FAISS", output_dir: Path, manifest: dict) -> None:
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    vector_store.save_local(str(output_dir))
    manifest_path = output_dir.parent / MANIFEST_FILENAME
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2))


def load_vector_store(output_dir: Path, embedding_model: str, api_key: str) -> "FAISS":
    if not output_dir.exists():
        raise FileNotFoundError(f"Vector store directory not found at {output_dir}")

    embeddings = _build_embeddings(embedding_model=embedding_model, api_key=api_key)
    faiss_class = _get_faiss_class()

    try:
        return faiss_class.load_local(
            str(output_dir),
            embeddings,
            allow_dangerous_deserialization=True,
        )
    except TypeError:
        return faiss_class.load_local(str(output_dir), embeddings)


def build_indexed_documents_frame(documents: list["Document"]) -> pd.DataFrame:
    rows = []
    for document in documents:
        row = {}
        for column in INDEXED_DOCUMENT_COLUMNS:
            if column == "text_for_embedding":
                row[column] = document.page_content
            elif column == "categories":
                row[column] = _normalize_categories(document.metadata.get(column))
            else:
                row[column] = _normalize_scalar(document.metadata.get(column))
        rows.append(row)
    return pd.DataFrame(rows, columns=INDEXED_DOCUMENT_COLUMNS)


def rebuild_index_artifacts(
    input_path: Path,
    output_dir: Path,
    embedding_model: str,
    api_key: str,
    batch_size: int = 50,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    rebuild_requested: bool = True,
) -> dict[str, Any]:
    frame = load_events_for_indexing(input_path)
    documents = build_documents(
        frame,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    vector_store = build_vector_store(
        documents=documents,
        embedding_model=embedding_model,
        api_key=api_key,
        batch_size=batch_size,
    )
    manifest = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "source_dataset": str(input_path),
        "output_dir": str(output_dir),
        "embedding_model": embedding_model,
        "batch_size": batch_size,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "indexed_event_count": len(frame),
        "indexed_document_count": len(documents),
        "rebuild_requested": rebuild_requested,
    }
    save_vector_store(vector_store, output_dir, manifest)

    indexed_documents_path = output_dir.parent / INDEXED_DOCUMENTS_FILENAME
    build_indexed_documents_frame(documents).to_parquet(indexed_documents_path, index=False)

    return {
        "manifest_path": str(output_dir.parent / MANIFEST_FILENAME),
        "indexed_documents_path": str(indexed_documents_path),
        "indexed_event_count": len(frame),
        "indexed_document_count": len(documents),
        "output_dir": str(output_dir),
        "manifest": manifest,
    }
