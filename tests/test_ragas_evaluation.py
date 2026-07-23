from __future__ import annotations

import csv
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import json
from pathlib import Path

import pandas as pd
import pytest

from openagenda_rag.ragas_evaluation import (
    METRIC_NAMES,
    RagasCase,
    build_evaluation_rows,
    interpret_score,
    load_ragas_cases,
    run_ragas_evaluation,
    summarize_ragas_scores,
    write_ragas_csv,
    write_ragas_json,
)


def _write_cases(path: Path, rows: list[tuple[str, str, str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["case_id", "question", "reference", "notes"])
        writer.writerows(rows)


def _three_cases() -> list[RagasCase]:
    return [
        RagasCase("a", "Question A", "Reference A", "note A"),
        RagasCase("b", "Question B", "Reference B", "note B"),
        RagasCase("c", "Question C", "Reference C", "note C"),
    ]


def _evaluation_rows() -> list[dict[str, object]]:
    return [
        {
            "case_id": case.case_id,
            "user_input": case.question,
            "retrieved_contexts": [f"Contexte {case.case_id.upper()}"],
            "response": f"Reponse {case.case_id.upper()}",
            "reference": case.reference,
            "source_titles": [f"Evenement {case.case_id.upper()}"],
            "notes": case.notes,
        }
        for case in _three_cases()
    ]


def test_ragas_case_is_frozen():
    case = _three_cases()[0]

    with pytest.raises(FrozenInstanceError):
        case.question = "Nouvelle question"


def test_load_ragas_cases_requires_three_complete_unique_cases(tmp_path: Path):
    path = tmp_path / "cases.csv"
    _write_cases(
        path,
        [
            ("a", "Question A", "Reference A", "note"),
            ("b", "Question B", "Reference B", "note"),
            ("c", "Question C", "Reference C", "note"),
        ],
    )

    cases = load_ragas_cases(path)

    assert [case.case_id for case in cases] == ["a", "b", "c"]


@pytest.mark.parametrize(
    "rows",
    [
        [
            ("a", "Question A", "Reference A", "note"),
            ("b", "Question B", "Reference B", "note"),
        ],
        [
            ("a", "Question A", "Reference A", "note"),
            ("b", "", "Reference B", "note"),
            ("c", "Question C", "Reference C", "note"),
        ],
        [
            ("a", "Question A", "Reference A", "note"),
            ("a", "Question B", "Reference B", "note"),
            ("c", "Question C", "Reference C", "note"),
        ],
    ],
)
def test_load_ragas_cases_rejects_incomplete_or_duplicate_cases(
    tmp_path: Path,
    rows: list[tuple[str, str, str, str]],
):
    path = tmp_path / "invalid.csv"
    _write_cases(path, rows)

    with pytest.raises(ValueError):
        load_ragas_cases(path)


def test_build_evaluation_rows_keeps_rag_fields():
    rows = build_evaluation_rows(
        [_three_cases()[0]],
        responder=lambda _: {
            "answer": "Reponse A",
            "retrieved_contexts": ["Contexte A"],
            "sources": [{"title": "Evenement A"}, {"title": ""}],
        },
    )

    assert rows == [
        {
            "case_id": "a",
            "user_input": "Question A",
            "retrieved_contexts": ["Contexte A"],
            "response": "Reponse A",
            "reference": "Reference A",
            "source_titles": ["Evenement A"],
            "notes": "note A",
        }
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {"answer": "", "retrieved_contexts": ["Contexte"], "sources": []},
        {"answer": "Reponse", "retrieved_contexts": [], "sources": []},
        {"answer": "Reponse", "retrieved_contexts": ["  "], "sources": []},
    ],
)
def test_build_evaluation_rows_rejects_empty_response_or_context(payload):
    with pytest.raises(ValueError, match="empty response or context"):
        build_evaluation_rows([_three_cases()[0]], responder=lambda _: payload)


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (1.0, "fort"),
        (0.8, "fort"),
        (0.7999, "acceptable"),
        (0.6, "acceptable"),
        (0.5999, "a ameliorer"),
    ],
)
def test_interpret_score_uses_documented_thresholds(score: float, expected: str):
    assert interpret_score(score) == expected


def test_summarize_ragas_scores_computes_metric_means():
    frame = pd.DataFrame(
        [
            {name: 1.0 if name == "faithfulness" else 0.8 for name in METRIC_NAMES},
            {name: 0.5 if name == "faithfulness" else 0.6 for name in METRIC_NAMES},
        ]
    )

    summary = summarize_ragas_scores(frame, METRIC_NAMES)

    assert summary == {
        "example_count": 2,
        "metric_means": {
            "faithfulness": 0.75,
            "answer_relevancy": 0.7,
            "context_precision": 0.7,
            "answer_correctness": 0.7,
        },
        "metric_interpretations": {
            "faithfulness": "acceptable",
            "answer_relevancy": "acceptable",
            "context_precision": "acceptable",
            "answer_correctness": "acceptable",
        },
    }


def test_summarize_ragas_scores_rejects_failed_metric():
    frame = pd.DataFrame([{name: 0.8 for name in METRIC_NAMES}])
    frame.loc[0, "faithfulness"] = None

    with pytest.raises(RuntimeError, match="faithfulness"):
        summarize_ragas_scores(frame, METRIC_NAMES)


def test_run_and_writers_serialize_complete_deterministic_results(tmp_path: Path):
    calls = []

    class FakeResult:
        def to_pandas(self):
            return pd.DataFrame(
                [
                    {
                        "faithfulness": 0.9,
                        "answer_relevancy": 0.8,
                        "context_precision": 0.7,
                        "answer_correctness": 0.6,
                    },
                    {name: 0.85 for name in METRIC_NAMES},
                    {name: 0.75 for name in METRIC_NAMES},
                ]
            )

    def fake_evaluate(*, dataset, metrics, llm, embeddings, run_config):
        calls.append(
            {
                "dataset": dataset,
                "metrics": metrics,
                "llm": llm,
                "embeddings": embeddings,
                "run_config": run_config,
            }
        )
        return FakeResult()

    generated_at = datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc)
    payload = run_ragas_evaluation(
        _evaluation_rows(),
        api_key="not-a-real-key",
        chat_model="judge-model",
        embedding_model="embedding-model",
        evaluation_callable=fake_evaluate,
        llm=object(),
        embeddings=object(),
        generated_at=generated_at,
    )

    output_json = tmp_path / "results.json"
    output_csv = tmp_path / "examples.csv"
    write_ragas_json(output_json, payload)
    write_ragas_csv(output_csv, payload["examples"])
    first_json = output_json.read_bytes()
    first_csv = output_csv.read_bytes()
    write_ragas_json(output_json, payload)
    write_ragas_csv(output_csv, payload["examples"])

    assert len(calls) == 1
    assert calls[0]["run_config"].max_workers == 1
    assert json.loads(first_json)["generated_at"] == "2026-07-23T12:00:00Z"
    assert json.loads(first_json)["models"] == {
        "chat": "judge-model",
        "embedding": "embedding-model",
    }
    assert json.loads(first_json)["metric_names"] == METRIC_NAMES
    assert len(payload["examples"]) == 3
    assert payload["examples"][0]["question"] == "Question A"
    assert payload["examples"][0]["user_input"] == "Question A"
    assert payload["examples"][0]["scores"]["faithfulness"] == 0.9
    assert payload["examples"][0]["interpretations"]["faithfulness"] == "fort"
    assert payload["examples"][0]["overall_interpretation"] == "acceptable"
    assert output_json.read_bytes() == first_json
    assert output_csv.read_bytes() == first_csv

    csv_rows = list(csv.DictReader(output_csv.open(encoding="utf-8")))
    assert len(csv_rows) == 3
    assert "Contexte A" in csv_rows[0]["retrieved_contexts"]
    assert csv_rows[0]["faithfulness"] == "0.9"
    assert csv_rows[0]["faithfulness_interpretation"] == "fort"
