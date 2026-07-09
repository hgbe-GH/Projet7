from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any
import ast
import re

from openagenda_rag.indexing import load_vector_store

if TYPE_CHECKING:
    from langchain_core.documents import Document


SYSTEM_PROMPT = """Tu es l'assistant de recommandation culturelle de Puls-Events.
Tu dois repondre uniquement a partir du contexte fourni.
Si le contexte ne permet pas de repondre, dis clairement que tu ne sais pas.
Fais des recommandations concretes, bien formulees, en citant les titres, lieux, dates et URLs quand ils existent.
N'invente ni evenement, ni date, ni lien."""


@dataclass
class SourceEntry:
    event_uid: str | None
    chunk_id: str | None
    title: str | None
    city: str | None
    location_name: str | None
    first_timing: str | None
    last_timing: str | None
    canonical_url: str | None
    categories: list[str]


def _get_chat_mistral_class():
    from langchain_mistralai import ChatMistralAI

    return ChatMistralAI


def _coerce_categories(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned or cleaned == "[]":
            return []
        matches = re.findall(r"'([^']*)'|\"([^\"]*)\"", cleaned)
        quoted_items = [left or right for left, right in matches if (left or right).strip()]
        if quoted_items:
            return quoted_items
        try:
            parsed = ast.literal_eval(cleaned)
        except (SyntaxError, ValueError):
            return [cleaned]
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
        if isinstance(parsed, tuple):
            return [str(item) for item in parsed]
        return [str(parsed)]
    if isinstance(value, list):
        normalized: list[str] = []
        for item in value:
            normalized.extend(_coerce_categories(item))
        return normalized
    if isinstance(value, tuple):
        normalized: list[str] = []
        for item in value:
            normalized.extend(_coerce_categories(item))
        return normalized
    return [str(value)]


def _coerce_response_text(response: Any) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(part.strip() for part in parts if part and part.strip())
    return str(content).strip()


def build_chat_model(
    model_name: str,
    api_key: str,
    temperature: float = 0.1,
    max_tokens: int = 700,
):
    if not api_key:
        raise ValueError("A Mistral API key is required to run the RAG chatbot.")

    chat_class = _get_chat_mistral_class()
    return chat_class(
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        random_seed=42,
    )


def build_retriever(
    index_output_dir: Path,
    embedding_model: str,
    api_key: str,
    top_k: int = 4,
):
    vector_store = load_vector_store(index_output_dir, embedding_model=embedding_model, api_key=api_key)
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": max(1, top_k)},
    )


def build_source_entries(documents: list["Document"]) -> list[SourceEntry]:
    entries: list[SourceEntry] = []
    seen_event_uids: set[str] = set()

    for document in documents:
        metadata = document.metadata or {}
        event_uid = metadata.get("event_uid")
        if event_uid in seen_event_uids:
            continue
        seen_event_uids.add(event_uid)
        entries.append(
            SourceEntry(
                event_uid=metadata.get("event_uid"),
                chunk_id=metadata.get("chunk_id"),
                title=metadata.get("title"),
                city=metadata.get("city"),
                location_name=metadata.get("location_name"),
                first_timing=metadata.get("first_timing"),
                last_timing=metadata.get("last_timing"),
                canonical_url=metadata.get("canonical_url"),
                categories=_coerce_categories(metadata.get("categories")),
            )
        )

    return entries


def format_documents_for_prompt(documents: list["Document"]) -> str:
    if not documents:
        return "Aucun evenement pertinent n'a ete retrouve."

    blocks = []
    for index, document in enumerate(documents, start=1):
        metadata = document.metadata or {}
        categories = ", ".join(_coerce_categories(metadata.get("categories"))) or "non renseignees"
        blocks.append(
            "\n".join(
                [
                    f"[Source {index}]",
                    f"Titre: {metadata.get('title') or 'inconnu'}",
                    f"Ville: {metadata.get('city') or 'inconnue'}",
                    f"Lieu: {metadata.get('location_name') or 'inconnu'}",
                    f"Debut: {metadata.get('first_timing') or 'inconnu'}",
                    f"Fin: {metadata.get('last_timing') or 'inconnue'}",
                    f"Categories: {categories}",
                    f"URL: {metadata.get('canonical_url') or 'indisponible'}",
                    "Contenu:",
                    document.page_content.strip(),
                ]
            )
        )
    return "\n\n".join(blocks)


def build_prompt() -> ChatPromptTemplate:
    from langchain_core.prompts import ChatPromptTemplate

    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                "Contexte:\n{context}\n\nQuestion utilisateur:\n{question}\n\n"
                "Reponds en francais, de maniere concise mais utile. "
                "Si tu recommandes des evenements, explique brievement pourquoi ils correspondent a la demande.",
            ),
        ]
    )


def answer_question(
    question: str,
    retriever: Any,
    chat_model: Any,
) -> dict[str, Any]:
    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("A non-empty question is required.")

    documents = list(retriever.invoke(cleaned_question))
    sources = build_source_entries(documents)
    if not documents:
        return {
            "question": cleaned_question,
            "answer": "Je ne sais pas, car aucun evenement pertinent n'a ete retrouve dans l'index.",
            "sources": [],
            "retrieved_chunk_count": 0,
        }

    prompt = build_prompt()
    messages = prompt.invoke(
        {
            "question": cleaned_question,
            "context": format_documents_for_prompt(documents),
        }
    )
    response = chat_model.invoke(messages)
    return {
        "question": cleaned_question,
        "answer": _coerce_response_text(response),
        "sources": [asdict(source) for source in sources],
        "retrieved_chunk_count": len(documents),
    }
