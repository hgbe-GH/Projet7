from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from openagenda_rag.ragas_evaluation import (  # noqa: E402
    build_evaluation_rows,
    load_ragas_cases,
    run_ragas_evaluation,
    write_ragas_csv,
    write_ragas_json,
)
from openagenda_rag.service import OpenAgendaRAGService  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate three factual OpenAgenda RAG cases with RAGAS and Mistral."
    )
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=PROJECT_ROOT / "tests/fixtures/ragas_eval_dataset.csv",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=PROJECT_ROOT / "outputs/evaluation/ragas_results.json",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=PROJECT_ROOT / "outputs/evaluation/ragas_examples.csv",
    )
    parser.add_argument(
        "--chat-model",
        default=os.getenv("RAG_EVALUATION_MODEL")
        or os.getenv("RAG_CHAT_MODEL")
        or "mistral-small-latest",
    )
    parser.add_argument(
        "--embedding-model",
        default=os.getenv("INDEX_EMBEDDING_MODEL", "mistral-embed"),
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    args = parse_args()
    api_key = os.getenv("MISTRAL_API_KEY") or os.getenv("MISTRALAI_API_KEY")
    if not api_key:
        raise SystemExit("MISTRAL_API_KEY is required.")

    service = OpenAgendaRAGService.from_env()
    cases = load_ragas_cases(args.dataset_path)
    print(f"Generating RAG answers and contexts for {len(cases)} cases...")
    rows = build_evaluation_rows(cases, service.ask_for_evaluation)
    print("Running RAGAS sequentially with Mistral...")
    payload = run_ragas_evaluation(
        rows,
        api_key=api_key,
        chat_model=args.chat_model,
        embedding_model=args.embedding_model,
        dataset_sha256=hashlib.sha256(args.dataset_path.read_bytes()).hexdigest(),
    )
    write_ragas_json(args.output_json, payload)
    write_ragas_csv(args.output_csv, payload["examples"])

    print(f"Examples: {payload['summary']['example_count']}")
    for name, score in payload["summary"]["metric_means"].items():
        label = payload["summary"]["metric_interpretations"][name]
        print(f"- {name}: {score:.3f} ({label})")
    print(f"JSON: {args.output_json}")
    print(f"CSV:  {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
