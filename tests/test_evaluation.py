from __future__ import annotations

from pathlib import Path

from openagenda_rag.evaluation import (
    EvaluationExample,
    build_output_payload,
    classify_result,
    evaluate_response,
    exact_match_soft,
    lexical_similarity,
    load_evaluation_examples,
    match_expected_titles,
    normalize_text,
    summarize_results,
)


def test_normalize_text_removes_case_accents_and_punctuation():
    assert normalize_text("Événement, à Paris !") == "evenement a paris"


def test_load_evaluation_examples_parses_json_title_lists(tmp_path: Path):
    dataset_path = tmp_path / "dataset.csv"
    dataset_path.write_text(
        "question,expected_answer,expected_event_titles,notes\n"
        '"Question","Attendu","[""Titre A"",""Titre B""]","note"\n',
        encoding="utf-8",
    )

    examples = load_evaluation_examples(dataset_path)

    assert examples == [
        EvaluationExample(
            question="Question",
            expected_answer="Attendu",
            expected_event_titles=["Titre A", "Titre B"],
            notes="note",
        )
    ]


def test_exact_match_soft_and_lexical_similarity_use_normalized_text():
    assert exact_match_soft("Je ne sais pas.", "je ne sais pas")
    assert lexical_similarity("concert a paris", "concert a paris ce soir") > 0.5


def test_match_expected_titles_looks_in_answer_and_sources():
    matches = match_expected_titles(
        ["Concert Fishers", "Expo Photo"],
        generated_answer="Je recommande Concert Fishers pour un public pop.",
        source_titles=["Autre evenement"],
    )

    assert matches == ["Concert Fishers"]


def test_classify_result_handles_positive_and_negative_cases():
    assert classify_result(
        expected_titles=["Concert Fishers"],
        exact_match=False,
        similarity=0.05,
        matched_titles=["Concert Fishers"],
        generated_answer="Je recommande Concert Fishers.",
    ) == "correct"
    assert classify_result(
        expected_titles=[],
        exact_match=False,
        similarity=0.1,
        matched_titles=[],
        generated_answer="Je ne sais pas, le corpus ne couvre pas cette ville.",
    ) == "correct"


def test_evaluate_response_and_summary_build_expected_metrics():
    example = EvaluationExample(
        question="Quels concerts recents a Paris ?",
        expected_answer="Le systeme doit recommander Concert Fishers.",
        expected_event_titles=["Concert Fishers"],
        notes="positive_precise",
    )
    response_payload = {
        "answer": "Je recommande Concert Fishers a Paris.",
        "sources": [{"title": "Concert Fishers"}],
    }

    result = evaluate_response(example, response_payload)
    summary = summarize_results([result])
    payload = build_output_payload(
        dataset_path=Path("tests/fixtures/rag_eval_dataset.csv"),
        mode="direct",
        results=[result],
        summary=summary,
        ragas_summary=None,
    )

    assert result.classification == "correct"
    assert result.matched_expected_titles == ["Concert Fishers"]
    assert summary["classification_counts"]["correct"] == 1
    assert payload["mode"] == "direct"
    assert payload["results"][0]["question"] == example.question
