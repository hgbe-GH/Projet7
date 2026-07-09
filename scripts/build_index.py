#!/usr/bin/env python
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from openagenda_rag.indexing import (
    INDEXED_DOCUMENTS_FILENAME,
    MANIFEST_FILENAME,
    build_documents,
    build_indexed_documents_frame,
    build_vector_store,
    load_events_for_indexing,
    save_vector_store,
)
from openagenda_rag.settings import load_index_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a FAISS index from normalized OpenAgenda events.")
    parser.add_argument("--input-path", type=Path, help="Path to the normalized events parquet file")
    parser.add_argument("--output-dir", type=Path, help="Directory where the FAISS index will be saved")
    parser.add_argument("--embedding-model", help="Mistral embedding model name")
    parser.add_argument("--batch-size", type=int, help="Number of documents to embed per batch")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Accepted for explicit full rebuilds; the command always replaces the target index directory.",
    )
    return parser.parse_args()


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return ROOT / path


def main() -> int:
    args = parse_args()
    settings = load_index_settings()

    input_path = _resolve_path(args.input_path or settings.input_path)
    output_dir = _resolve_path(args.output_dir or settings.output_dir)
    embedding_model = args.embedding_model or settings.embedding_model
    batch_size = args.batch_size or settings.batch_size
    api_key = settings.mistral_api_key

    try:
        frame = load_events_for_indexing(input_path)
    except Exception as exc:  # pragma: no cover - CLI integration path
        print(f"Index build failed: {exc}", file=sys.stderr)
        return 1

    if not api_key:
        print("MISTRAL_API_KEY or MISTRALAI_API_KEY is required to build the FAISS index.", file=sys.stderr)
        return 1

    try:
        documents = build_documents(frame)
        vector_store = build_vector_store(
            documents=documents,
            embedding_model=embedding_model,
            api_key=api_key,
            batch_size=batch_size,
        )
    except Exception as exc:  # pragma: no cover - CLI integration path
        print(f"Index build failed: {exc}", file=sys.stderr)
        return 1

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_dataset": str(input_path),
        "output_dir": str(output_dir),
        "embedding_model": embedding_model,
        "batch_size": batch_size,
        "indexed_event_count": len(frame),
        "indexed_document_count": len(documents),
        "rebuild_requested": args.rebuild,
    }
    save_vector_store(vector_store, output_dir, manifest)

    indexed_documents_path = output_dir.parent / INDEXED_DOCUMENTS_FILENAME
    build_indexed_documents_frame(frame).to_parquet(indexed_documents_path, index=False)

    print(
        json.dumps(
            {
                "manifest_path": str(output_dir.parent / MANIFEST_FILENAME),
                "indexed_documents_path": str(indexed_documents_path),
                "indexed_event_count": len(frame),
                "indexed_document_count": len(documents),
                "output_dir": str(output_dir),
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
