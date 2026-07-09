#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from openagenda_rag.rag import answer_question, build_chat_model, build_retriever
from openagenda_rag.settings import load_rag_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the OpenAgenda RAG chatbot against the local FAISS index.")
    parser.add_argument("--question", help="One-shot user question. If omitted, an interactive prompt starts.")
    parser.add_argument("--index-dir", type=Path, help="Path to the persisted FAISS index directory")
    parser.add_argument("--embedding-model", help="Embedding model used to load the vector store")
    parser.add_argument("--chat-model", help="Mistral chat model name")
    parser.add_argument("--top-k", type=int, help="Number of chunks to retrieve")
    parser.add_argument("--temperature", type=float, help="LLM temperature")
    parser.add_argument("--max-tokens", type=int, help="Maximum output tokens")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full response payload as JSON instead of a formatted text block.",
    )
    return parser.parse_args()


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return ROOT / path


def _format_text_response(payload: dict) -> str:
    lines = [payload["answer"].strip(), "", "Sources:"]
    if not payload["sources"]:
        lines.append("- aucune source")
        return "\n".join(lines)

    for source in payload["sources"]:
        label = source.get("title") or source.get("event_uid") or "source"
        city = source.get("city") or "ville inconnue"
        first_timing = source.get("first_timing") or "date inconnue"
        url = source.get("canonical_url") or "URL indisponible"
        lines.append(f"- {label} | {city} | {first_timing} | {url}")
    return "\n".join(lines)


def _run_one_question(question: str, retriever, chat_model, as_json: bool) -> int:
    payload = answer_question(question=question, retriever=retriever, chat_model=chat_model)
    if as_json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(_format_text_response(payload))
    return 0


def main() -> int:
    args = parse_args()
    settings = load_rag_settings()

    api_key = settings.mistral_api_key
    if not api_key:
        print("MISTRAL_API_KEY or MISTRALAI_API_KEY is required to run the chatbot.", file=sys.stderr)
        return 1

    index_dir = _resolve_path(args.index_dir or settings.index_output_dir)
    embedding_model = args.embedding_model or settings.embedding_model
    chat_model_name = args.chat_model or settings.chat_model
    top_k = args.top_k or settings.top_k
    temperature = args.temperature if args.temperature is not None else settings.temperature
    max_tokens = args.max_tokens or settings.max_tokens

    try:
        retriever = build_retriever(
            index_output_dir=index_dir,
            embedding_model=embedding_model,
            api_key=api_key,
            top_k=top_k,
        )
        chat_model = build_chat_model(
            model_name=chat_model_name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as exc:  # pragma: no cover - CLI integration path
        print(f"Chatbot initialization failed: {exc}", file=sys.stderr)
        return 1

    if args.question:
        try:
            return _run_one_question(args.question, retriever, chat_model, args.json)
        except Exception as exc:  # pragma: no cover - CLI integration path
            print(f"Chatbot request failed: {exc}", file=sys.stderr)
            return 1

    print("Interactive mode. Press Enter on an empty line or type 'exit' to quit.")
    while True:
        try:
            question = input("> ").strip()
        except EOFError:
            print()
            return 0
        if not question or question.lower() in {"exit", "quit"}:
            return 0
        try:
            _run_one_question(question, retriever, chat_model, args.json)
        except Exception as exc:  # pragma: no cover - CLI integration path
            print(f"Chatbot request failed: {exc}", file=sys.stderr)
            return 1
        print()


if __name__ == "__main__":
    raise SystemExit(main())
