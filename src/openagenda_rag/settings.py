from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import os
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_LOOKBACK_DAYS = 365


@dataclass
class FetchSettings:
    opendatasoft_base_url: str
    opendatasoft_dataset: str
    agenda_uid: str | None
    agenda_search: str | None
    city: str | None
    start_date: str
    end_date: str | None
    category_field: str | None
    category_ids: list[str]
    mistral_api_key: str | None


@dataclass
class IndexSettings:
    input_path: Path
    output_dir: Path
    embedding_model: str
    batch_size: int
    chunk_size: int
    chunk_overlap: int
    mistral_api_key: str | None


@dataclass
class RagSettings:
    index_output_dir: Path
    embedding_model: str
    chat_model: str
    top_k: int
    temperature: float
    max_tokens: int
    mistral_api_key: str | None


@dataclass
class ApiSettings:
    host: str
    port: int
    rebuild_token: str | None


def _default_start_date() -> str:
    return (date.today() - timedelta(days=DEFAULT_LOOKBACK_DAYS)).isoformat()


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def load_fetch_settings() -> FetchSettings:
    load_dotenv()
    return FetchSettings(
        opendatasoft_base_url=os.getenv("OPENDATASOFT_BASE_URL", "https://public.opendatasoft.com/api/explore/v2.1"),
        opendatasoft_dataset=os.getenv("OPENDATASOFT_DATASET", "evenements-publics-openagenda"),
        agenda_uid=os.getenv("OPENAGENDA_AGENDA_UID"),
        agenda_search=os.getenv("OPENAGENDA_SEARCH"),
        city=os.getenv("OPENAGENDA_CITY"),
        start_date=os.getenv("OPENAGENDA_START_DATE", _default_start_date()),
        end_date=os.getenv("OPENAGENDA_END_DATE") or None,
        category_field=os.getenv("OPENAGENDA_CATEGORY_FIELD") or None,
        category_ids=_split_csv(os.getenv("OPENAGENDA_CATEGORY_IDS")),
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
    )


def load_index_settings() -> IndexSettings:
    load_dotenv()
    return IndexSettings(
        input_path=Path(os.getenv("INDEX_INPUT_PATH", "data/processed/events.parquet")),
        output_dir=Path(os.getenv("INDEX_OUTPUT_DIR", "data/index/faiss")),
        embedding_model=os.getenv("INDEX_EMBEDDING_MODEL", "mistral-embed"),
        batch_size=int(os.getenv("INDEX_BATCH_SIZE", "50")),
        chunk_size=int(os.getenv("INDEX_CHUNK_SIZE", "1000")),
        chunk_overlap=int(os.getenv("INDEX_CHUNK_OVERLAP", "200")),
        mistral_api_key=os.getenv("MISTRAL_API_KEY") or os.getenv("MISTRALAI_API_KEY"),
    )


def load_rag_settings() -> RagSettings:
    load_dotenv()
    return RagSettings(
        index_output_dir=Path(os.getenv("INDEX_OUTPUT_DIR", "data/index/faiss")),
        embedding_model=os.getenv("INDEX_EMBEDDING_MODEL", "mistral-embed"),
        chat_model=os.getenv("RAG_CHAT_MODEL", "mistral-small-latest"),
        top_k=int(os.getenv("RAG_TOP_K", "4")),
        temperature=float(os.getenv("RAG_TEMPERATURE", "0.1")),
        max_tokens=int(os.getenv("RAG_MAX_TOKENS", "700")),
        mistral_api_key=os.getenv("MISTRAL_API_KEY") or os.getenv("MISTRALAI_API_KEY"),
    )


def load_api_settings() -> ApiSettings:
    load_dotenv()
    return ApiSettings(
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", "8000")),
        rebuild_token=os.getenv("API_REBUILD_TOKEN") or None,
    )
