from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio
import importlib.metadata
import json
import math
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence
import pandas as pd

METRIC_NAMES = [
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "answer_correctness",
]


@dataclass(frozen=True)
class RagasCase:
    case_id: str
    question: str
    reference: str
    notes: str


def load_ragas_cases(path: Path) -> list[RagasCase]:
    if not path.is_file():
        raise FileNotFoundError(f"RAGAS dataset not found: {path}")

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"case_id", "question", "reference", "notes"}
        if set(reader.fieldnames or []) != required:
            raise ValueError(f"RAGAS dataset must contain exactly: {sorted(required)}")
        cases = [
            RagasCase(
                case_id=(row["case_id"] or "").strip(),
                question=(row["question"] or "").strip(),
                reference=(row["reference"] or "").strip(),
                notes=(row["notes"] or "").strip(),
            )
            for row in reader
        ]

    if len(cases) < 3:
        raise ValueError("RAGAS dataset must contain at least three cases.")
    if any(not all((case.case_id, case.question, case.reference, case.notes)) for case in cases):
        raise ValueError("Every RAGAS case must be complete.")
    if len({case.case_id for case in cases}) != len(cases):
        raise ValueError("RAGAS case_id values must be unique.")
    return cases


def build_evaluation_rows(
    cases: Iterable[RagasCase],
    responder: Callable[[str], dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        payload = responder(case.question)
        response = str(payload.get("answer") or "").strip()
        contexts = [
            str(context).strip()
            for context in payload.get("retrieved_contexts", [])
            if str(context).strip()
        ]
        if not response or not contexts:
            raise ValueError(f"Case {case.case_id} has an empty response or context.")
        source_titles = [
            str(source.get("title") or "").strip()
            for source in payload.get("sources", [])
            if str(source.get("title") or "").strip()
        ]
        rows.append(
            {
                "case_id": case.case_id,
                "user_input": case.question,
                "retrieved_contexts": contexts,
                "response": response,
                "reference": case.reference,
                "source_titles": source_titles,
                "notes": case.notes,
            }
        )
    return rows


def interpret_score(score: float) -> str:
    if score >= 0.8:
        return "fort"
    if score >= 0.6:
        return "acceptable"
    return "a ameliorer"


def _validated_score(value: Any, metric_name: str) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"RAGAS metric {metric_name} did not return a numeric score.") from exc
    if not math.isfinite(score):
        raise RuntimeError(f"RAGAS metric {metric_name} failed.")
    return round(score, 6)


def summarize_ragas_scores(
    frame: pd.DataFrame,
    metric_names: Sequence[str] = METRIC_NAMES,
) -> dict[str, Any]:
    means: dict[str, float] = {}
    for name in metric_names:
        if name not in frame.columns or frame[name].isna().any():
            raise RuntimeError(f"RAGAS metric {name} failed.")
        values = [_validated_score(value, name) for value in frame[name]]
        means[name] = round(sum(values) / len(values), 6)
    return {
        "example_count": len(frame),
        "metric_means": means,
        "metric_interpretations": {
            name: interpret_score(score) for name, score in means.items()
        },
    }


def _default_ragas_runtime(
    api_key: str,
    chat_model: str,
    embedding_model: str,
) -> tuple[Any, Any, list[Any]]:
    from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings
    from ragas.embeddings import BaseRagasEmbedding
    from ragas.llms import InstructorBaseRagasLLM
    from ragas.metrics.collections import (
        AnswerCorrectness,
        AnswerRelevancy,
        ContextPrecision,
        Faithfulness,
    )

    class MistralStructuredLLM(InstructorBaseRagasLLM):
        def __init__(self) -> None:
            self.client = ChatMistralAI(
                model=chat_model,
                mistral_api_key=api_key,
                temperature=0,
            )

        def generate(self, prompt: str, response_model: type[Any]) -> Any:
            return self.client.with_structured_output(
                response_model,
                method="function_calling",
            ).invoke(prompt)

        async def agenerate(self, prompt: str, response_model: type[Any]) -> Any:
            return await self.client.with_structured_output(
                response_model,
                method="function_calling",
            ).ainvoke(prompt)

    class MistralEmbeddingAdapter(BaseRagasEmbedding):
        def __init__(self) -> None:
            super().__init__()
            self.client = MistralAIEmbeddings(
                model=embedding_model,
                mistral_api_key=api_key,
            )

        def embed_text(self, text: str, **kwargs: Any) -> list[float]:
            return self.client.embed_query(text)

        async def aembed_text(self, text: str, **kwargs: Any) -> list[float]:
            return await self.client.aembed_query(text)

    llm = MistralStructuredLLM()
    embeddings = MistralEmbeddingAdapter()
    metrics = [
        Faithfulness(llm=llm),
        AnswerRelevancy(llm=llm, embeddings=embeddings),
        ContextPrecision(llm=llm),
        AnswerCorrectness(llm=llm, embeddings=embeddings),
    ]
    return llm, embeddings, metrics


async def _score_rows_with_modern_metrics(
    rows: list[dict[str, Any]],
    metrics: Sequence[Any],
    *,
    max_attempts: int = 3,
    retry_delay_seconds: float = 2.0,
) -> pd.DataFrame:
    async def call_with_retry(metric: Any, **kwargs: Any) -> Any:
        for attempt in range(max_attempts):
            try:
                return await metric.ascore(**kwargs)
            except Exception:
                if attempt + 1 >= max_attempts:
                    raise
                await asyncio.sleep(retry_delay_seconds * (2**attempt))
        raise RuntimeError("Unreachable retry state.")

    score_rows: list[dict[str, float]] = []
    for row in rows:
        common = {
            "user_input": row["user_input"],
            "response": row["response"],
            "retrieved_contexts": row["retrieved_contexts"],
            "reference": row["reference"],
        }
        values: dict[str, float] = {}
        for name, metric in zip(METRIC_NAMES, metrics, strict=True):
            if name == "faithfulness":
                result = await call_with_retry(
                    metric,
                    user_input=common["user_input"],
                    response=common["response"],
                    retrieved_contexts=common["retrieved_contexts"],
                )
            elif name == "answer_relevancy":
                result = await call_with_retry(
                    metric,
                    user_input=common["user_input"],
                    response=common["response"],
                )
            elif name == "context_precision":
                result = await call_with_retry(
                    metric,
                    user_input=common["user_input"],
                    reference=common["reference"],
                    retrieved_contexts=common["retrieved_contexts"],
                )
            else:
                result = await call_with_retry(
                    metric,
                    user_input=common["user_input"],
                    response=common["response"],
                    reference=common["reference"],
                )
            values[name] = _validated_score(result.value, name)
        score_rows.append(values)
    return pd.DataFrame(score_rows)


def run_ragas_evaluation(
    rows: list[dict[str, Any]],
    *,
    api_key: str,
    chat_model: str,
    embedding_model: str,
    evaluation_callable: Callable[..., Any] | None = None,
    llm: Any | None = None,
    embeddings: Any | None = None,
    generated_at: datetime | None = None,
    dataset_sha256: str | None = None,
) -> dict[str, Any]:
    if not api_key:
        raise ValueError("MISTRAL_API_KEY is required for RAGAS evaluation.")
    if not rows:
        raise ValueError("At least one evaluation row is required.")

    metrics: list[Any]
    if llm is None or embeddings is None:
        llm, embeddings, metrics = _default_ragas_runtime(
            api_key,
            chat_model,
            embedding_model,
        )
    else:
        metrics = list(METRIC_NAMES)

    if evaluation_callable is None:
        score_frame = asyncio.run(_score_rows_with_modern_metrics(rows, metrics))
    else:
        from ragas import EvaluationDataset
        from ragas.run_config import RunConfig

        samples = [
            {
                key: row[key]
                for key in ("user_input", "retrieved_contexts", "response", "reference")
            }
            for row in rows
        ]
        dataset = EvaluationDataset.from_list(samples)
        result = evaluation_callable(
            dataset=dataset,
            metrics=metrics,
            llm=llm,
            embeddings=embeddings,
            run_config=RunConfig(timeout=180, max_retries=5, max_workers=1),
        )
        score_frame = result.to_pandas()
    summary = summarize_ragas_scores(score_frame, METRIC_NAMES)

    examples: list[dict[str, Any]] = []
    for row, (_, scores_row) in zip(rows, score_frame.iterrows(), strict=True):
        scores = {
            name: _validated_score(scores_row[name], name) for name in METRIC_NAMES
        }
        mean_score = round(sum(scores.values()) / len(scores), 6)
        examples.append(
            {
                "case_id": row["case_id"],
                "question": row["user_input"],
                "user_input": row["user_input"],
                "contexts": row["retrieved_contexts"],
                "retrieved_contexts": row["retrieved_contexts"],
                "response": row["response"],
                "reference": row["reference"],
                "source_titles": row["source_titles"],
                "notes": row["notes"],
                "scores": scores,
                "interpretations": {
                    name: interpret_score(score) for name, score in scores.items()
                },
                "overall_score": mean_score,
                "overall_interpretation": interpret_score(mean_score),
            }
        )

    timestamp = generated_at or datetime.now(timezone.utc)
    return {
        "generated_at": timestamp.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "models": {"chat": chat_model, "embedding": embedding_model},
        "provenance": {
            "ragas_version": importlib.metadata.version("ragas"),
            "dataset_sha256": dataset_sha256,
        },
        "metric_names": list(METRIC_NAMES),
        "summary": summary,
        "examples": examples,
    }


def write_ragas_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_ragas_csv(path: Path, examples: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "case_id",
        "question",
        "retrieved_contexts",
        "response",
        "reference",
        "source_titles",
        *METRIC_NAMES,
        *(f"{name}_interpretation" for name in METRIC_NAMES),
        "overall_score",
        "overall_interpretation",
        "notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for example in examples:
            writer.writerow(
                {
                    "case_id": example["case_id"],
                    "question": example["question"],
                    "retrieved_contexts": "\n\n".join(example["retrieved_contexts"]),
                    "response": example["response"],
                    "reference": example["reference"],
                    "source_titles": " | ".join(example["source_titles"]),
                    **example["scores"],
                    **{
                        f"{name}_interpretation": value
                        for name, value in example["interpretations"].items()
                    },
                    "overall_score": example["overall_score"],
                    "overall_interpretation": example["overall_interpretation"],
                    "notes": example["notes"],
                }
            )
