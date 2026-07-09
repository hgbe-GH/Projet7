#!/usr/bin/env python
from __future__ import annotations

import os
import sys
from pathlib import Path
import warnings

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def check_imports() -> None:
    warnings.filterwarnings(
        "ignore",
        message=r"`langchain-community` is being sunset.*",
        category=DeprecationWarning,
    )
    import faiss  # noqa: F401
    import fastapi  # noqa: F401
    from langchain_community.vectorstores import FAISS  # noqa: F401
    from langchain_huggingface import HuggingFaceEmbeddings  # noqa: F401
    from langchain_mistralai import MistralAIEmbeddings  # noqa: F401
    from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: F401
    from mistralai.client import Mistral  # noqa: F401
    import uvicorn  # noqa: F401

    print(
        "[ok] Core imports succeeded: fastapi, uvicorn, faiss, FAISS vectorstore, text splitter, HuggingFace embeddings, Mistral integrations"
    )


def check_mistral_api() -> None:
    from mistralai.client import Mistral

    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("[skip] MISTRAL_API_KEY not set; real Mistral embedding smoke test skipped")
        return

    with Mistral(api_key=api_key) as client:
        response = client.embeddings.create(
            model="mistral-embed",
            inputs=["Smoke test from OpenAgenda RAG setup."],
        )
    embedding = response.data[0].embedding
    print(f"[ok] Mistral embedding smoke test succeeded with vector size {len(embedding)}")


def main() -> int:
    load_dotenv()
    try:
        check_imports()
        check_mistral_api()
    except Exception as exc:  # pragma: no cover - smoke script
        print(f"[error] Environment check failed: {exc}", file=sys.stderr)
        return 1

    if os.getenv("OPENAGENDA_API_KEY"):
        print("[info] OPENAGENDA_API_KEY detected; native OpenAgenda API access is available if you add custom scripts later")
    else:
        print("[ok] No OPENAGENDA_API_KEY set; the public Opendatasoft dataset remains usable for stage 2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
