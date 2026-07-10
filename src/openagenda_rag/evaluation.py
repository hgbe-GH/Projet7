from __future__ import annotations

from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
import csv
import json
import re
from pathlib import Path
from typing import Any, Callable
import unicodedata

import httpx

from openagenda_rag.service import OpenAgendaRAGService


DEFAULT_EVAL_DATASET_PATH = Path("tests/fixtures/rag_eval_dataset.csv")
DEFAULT_EVAL_OUTPUT_PATH = Path("outputs/evaluation/latest_results.json")
DEFAULT_EVAL_SUMMARY_PATH = Path("outputs/evaluation/latest_summary.json")


@dataclass
class EvaluationExample:
    question: str
    expected_answer: str
    expected_event_titles: list[str]
    notes: str


@dataclass
class EvaluationResult:
    question: str
    expected_answer: str
    expected_event_titles: list[str]
    notes: str
    generated_answer: str
    source_titles: list[str]
    exact_match_soft: bool
    lexical_similarity: float
    matched_expected_titles: list[str]
    matched_expected_titles_count: int
    classification: str


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def parse_expected_titles(value: str | None) -> list[str]:
    if not value:
        return []
    cleaned = value.strip()
    if not cleaned:
        return []
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return [item.strip() for item in cleaned.split("|") if item.strip()]
    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]
    return [str(parsed).strip()] if str(parsed).strip() else []


def load_evaluation_examples(dataset_path: Path) -> list[EvaluationExample]:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Annotated evaluation dataset not found at {dataset_path}")

    examples: list[EvaluationExample] = []
    with dataset_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required_columns = {"question", "expected_answer", "expected_event_titles", "notes"}
        if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
            raise ValueError(
                "Evaluation dataset must define the columns: question, expected_answer, expected_event_titles, notes"
            )
        for row in reader:
            question = (row.get("question") or "").strip()
            expected_answer = (row.get("expected_answer") or "").strip()
            if not question or not expected_answer:
                continue
            examples.append(
                EvaluationExample(
                    question=question,
                    expected_answer=expected_answer,
                    expected_event_titles=parse_expected_titles(row.get("expected_event_titles")),
                    notes=(row.get("notes") or "").strip(),
                )
            )
    if not examples:
        raise ValueError(f"No evaluation examples could be loaded from {dataset_path}")
    return examples


def exact_match_soft(expected_answer: str, generated_answer: str) -> bool:
    return normalize_text(expected_answer) == normalize_text(generated_answer)


def lexical_similarity(expected_answer: str, generated_answer: str) -> float:
    return SequenceMatcher(None, normalize_text(expected_answer), normalize_text(generated_answer)).ratio()


def match_expected_titles(expected_titles: list[str], generated_answer: str, source_titles: list[str]) -> list[str]:
    normalized_answer = normalize_text(generated_answer)
    normalized_sources = [normalize_text(title) for title in source_titles if normalize_text(title)]
    matches: list[str] = []
    for title in expected_titles:
        normalized_title = normalize_text(title)
        if not normalized_title:
            continue
        if normalized_title in normalized_answer or any(normalized_title in source for source in normalized_sources):
            matches.append(title)
    return matches


def classify_result(
    *,
    expected_titles: list[str],
    exact_match: bool,
    similarity: float,
    matched_titles: list[str],
    generated_answer: str,
) -> str:
    normalized_generated = normalize_text(generated_answer)
    negative_signal = any(
        signal in normalized_generated for signal in ("je ne sais pas", "aucun evenement", "pas d evenement")
    )

    if not expected_titles:
        if exact_match or negative_signal:
            return "correct"
        if similarity >= 0.35:
            return "partial"
        return "incorrect"

    if len(matched_titles) == len(expected_titles) and normalized_generated:
        return "correct"
    if matched_titles or similarity >= 0.35:
        return "partial"
    return "incorrect"


def evaluate_response(example: EvaluationExample, response_payload: dict[str, Any]) -> EvaluationResult:
    generated_answer = str(response_payload.get("answer") or "").strip()
    source_titles = [
        str(source.get("title")).strip()
        for source in response_payload.get("sources", [])
        if str(source.get("title") or "").strip()
    ]
    exact = exact_match_soft(example.expected_answer, generated_answer)
    similarity = lexical_similarity(example.expected_answer, generated_answer)
    matched_titles = match_expected_titles(example.expected_event_titles, generated_answer, source_titles)
    classification = classify_result(
        expected_titles=example.expected_event_titles,
        exact_match=exact,
        similarity=similarity,
        matched_titles=matched_titles,
        generated_answer=generated_answer,
    )
    return EvaluationResult(
        question=example.question,
        expected_answer=example.expected_answer,
        expected_event_titles=example.expected_event_titles,
        notes=example.notes,
        generated_answer=generated_answer,
        source_titles=source_titles,
        exact_match_soft=exact,
        lexical_similarity=round(similarity, 4),
        matched_expected_titles=matched_titles,
        matched_expected_titles_count=len(matched_titles),
        classification=classification,
    )


def summarize_results(results: list[EvaluationResult]) -> dict[str, Any]:
    total = len(results)
    counts = {"correct": 0, "partial": 0, "incorrect": 0}
    exact_matches = 0
    similarity_sum = 0.0
    title_hit_cases = 0

    for result in results:
        counts[result.classification] = counts.get(result.classification, 0) + 1
        exact_matches += int(result.exact_match_soft)
        similarity_sum += result.lexical_similarity
        if result.matched_expected_titles_count > 0:
            title_hit_cases += 1

    return {
        "total_examples": total,
        "classification_counts": counts,
        "exact_match_soft_rate": round(exact_matches / total, 4) if total else 0.0,
        "average_lexical_similarity": round(similarity_sum / total, 4) if total else 0.0,
        "title_hit_case_rate": round(title_hit_cases / total, 4) if total else 0.0,
    }


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return Path.cwd() / path


def direct_responder_factory() -> Callable[[str], dict[str, Any]]:
    service = OpenAgendaRAGService.from_env()
    return service.ask


def api_responder_factory(base_url: str, timeout_seconds: float = 120.0) -> Callable[[str], dict[str, Any]]:
    client = httpx.Client(base_url=base_url, timeout=httpx.Timeout(timeout_seconds))

    def ask(question: str) -> dict[str, Any]:
        response = client.post("/ask", json={"question": question})
        response.raise_for_status()
        return response.json()

    return ask


def run_evaluation(
    examples: list[EvaluationExample],
    responder: Callable[[str], dict[str, Any]],
) -> tuple[list[EvaluationResult], dict[str, Any]]:
    results = [evaluate_response(example, responder(example.question)) for example in examples]
    return results, summarize_results(results)


def build_output_payload(
    dataset_path: Path,
    mode: str,
    results: list[EvaluationResult],
    summary: dict[str, Any],
    ragas_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "dataset_path": str(dataset_path),
        "mode": mode,
        "results": [asdict(result) for result in results],
        "summary": summary,
    }
    if ragas_summary is not None:
        payload["ragas"] = ragas_summary
    return payload


def write_evaluation_outputs(
    output_path: Path,
    summary_path: Path,
    payload: dict[str, Any],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2))
    summary_path.write_text(json.dumps(payload["summary"], ensure_ascii=True, indent=2))


def maybe_collect_ragas_summary(results: list[EvaluationResult]) -> dict[str, Any]:
    try:
        import ragas  # noqa: F401
    except ImportError:
        return {"enabled": False, "status": "skipped", "reason": "ragas not installed"}

    return {
        "enabled": True,
        "status": "skipped",
        "reason": "ragas integration not configured in this POC; local deterministic metrics remain the source of truth",
        "evaluated_examples": len(results),
    }
