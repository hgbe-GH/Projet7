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

from openagenda_rag.evaluation import (
    DEFAULT_EVAL_DATASET_PATH,
    DEFAULT_EVAL_OUTPUT_PATH,
    DEFAULT_EVAL_SUMMARY_PATH,
    api_responder_factory,
    build_output_payload,
    direct_responder_factory,
    load_evaluation_examples,
    maybe_collect_ragas_summary,
    run_evaluation,
    write_evaluation_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the OpenAgenda RAG system against an annotated dataset.")
    parser.add_argument("--dataset-path", type=Path, default=DEFAULT_EVAL_DATASET_PATH)
    parser.add_argument("--mode", choices=["direct", "api"], default="direct")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Used only in api mode")
    parser.add_argument("--output-path", type=Path, default=DEFAULT_EVAL_OUTPUT_PATH)
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_EVAL_SUMMARY_PATH)
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP timeout in api mode")
    parser.add_argument("--ragas", action="store_true", help="Collect optional Ragas availability metadata")
    return parser.parse_args()


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return ROOT / path


def main() -> int:
    args = parse_args()
    dataset_path = _resolve_path(args.dataset_path)
    output_path = _resolve_path(args.output_path)
    summary_path = _resolve_path(args.summary_path)

    try:
        examples = load_evaluation_examples(dataset_path)
        responder = (
            api_responder_factory(base_url=args.base_url, timeout_seconds=args.timeout)
            if args.mode == "api"
            else direct_responder_factory()
        )
        results, summary = run_evaluation(examples, responder)
        ragas_summary = maybe_collect_ragas_summary(results) if args.ragas else None
        payload = build_output_payload(
            dataset_path=dataset_path,
            mode=args.mode,
            results=results,
            summary=summary,
            ragas_summary=ragas_summary,
        )
        write_evaluation_outputs(output_path=output_path, summary_path=summary_path, payload=payload)
    except Exception as exc:  # pragma: no cover - CLI integration path
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"dataset_path": str(dataset_path), "mode": args.mode, "summary": summary}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
