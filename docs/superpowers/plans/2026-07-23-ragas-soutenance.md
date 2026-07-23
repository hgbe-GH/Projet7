# RAGAS et soutenance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produire une evaluation RAGAS reelle sur trois cas et finaliser une demonstration API, un rapport technique, un deck de quinze slides et les supports d'une soutenance de quinze minutes.

**Architecture:** Le moteur RAG existant conserve son API publique et expose en interne les contextes recuperes pour l'evaluation. Un module RAGAS dedie transforme les reponses en `SingleTurnSample`, execute quatre metriques avec les modeles Mistral existants et serialise les resultats. Les livrables DOCX et PPTX consomment uniquement les artefacts mesures afin de ne jamais afficher de score invente.

**Tech Stack:** Python 3.12, LangChain, Mistral, FAISS, Ragas 0.4.3, FastAPI, httpx, pytest, python-docx, Docker, PowerPoint Artifact Tool.

---

## File Map

- Modify `requirements.txt`: ajouter Ragas et python-docx avec des versions figees.
- Modify `environment.yml`: installer les dependances pip lors de la creation Conda.
- Modify `src/openagenda_rag/rag.py`: exposer facultativement les contextes recuperes sans changer `/ask`.
- Modify `src/openagenda_rag/service.py`: ajouter `ask_for_evaluation`.
- Create `src/openagenda_rag/ragas_evaluation.py`: charger les cas, executer RAGAS, interpreter et serialiser les scores.
- Create `scripts/evaluate_ragas.py`: CLI officielle de l'evaluation RAGAS.
- Create `tests/fixtures/ragas_eval_dataset.csv`: trois references factuelles.
- Create `tests/test_ragas_evaluation.py`: tests reseau-off du pipeline RAGAS.
- Create `src/openagenda_rag/demo.py`: logique testable de demonstration chronometree.
- Create `scripts/demo_api_5min.py`: CLI de demonstration.
- Create `scripts/demo_api_5min.sh`: point d'entree simple pour la soutenance.
- Create `tests/test_demo.py`: tests du cas nominal, du cas limite et de la limite de temps.
- Create `docs/soutenance/script_soutenance_15min.md`: texte oral chronometre.
- Create `docs/soutenance/questions_reponses.md`: douze questions et reponses.
- Create `scripts/build_report.py`: generation reproductible du rapport depuis le modele.
- Create `outputs/rapport-technique-openagenda-rag.docx`: rapport final.
- Modify `outputs/openagenda-rag-soutenance.pptx`: deck final de quinze slides.
- Modify `README.md`: commandes RAGAS, demonstration et livrables.

### Task 1: Exposer les contextes recuperes sans modifier l'API

**Files:**
- Modify: `src/openagenda_rag/rag.py:191-223`
- Modify: `src/openagenda_rag/service.py:51-53`
- Test: `tests/test_rag.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write the failing test for evaluation contexts**

Ajouter dans `tests/test_rag.py` :

```python
def test_answer_question_can_include_retrieved_contexts_for_evaluation():
    documents = _sample_documents()
    payload = answer_question(
        question="Je cherche un concert a Paris",
        retriever=FakeRetriever(documents),
        chat_model=FakeChatModel("Je recommande Concert jazz."),
        include_contexts=True,
    )

    assert payload["retrieved_contexts"] == [doc.page_content for doc in documents]
    assert payload["retrieved_chunk_count"] == len(documents)
```

Ajouter aussi :

```python
def test_answer_question_does_not_expose_contexts_by_default():
    payload = answer_question(
        question="Je cherche un concert a Paris",
        retriever=FakeRetriever(_sample_documents()),
        chat_model=FakeChatModel("Je recommande Concert jazz."),
    )

    assert "retrieved_contexts" not in payload
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
conda run -n openagenda-rag env PYTHONNOUSERSITE=1 \
  python -m pytest -q \
  tests/test_rag.py::test_answer_question_can_include_retrieved_contexts_for_evaluation \
  tests/test_rag.py::test_answer_question_does_not_expose_contexts_by_default
```

Expected: FAIL because `answer_question` does not accept `include_contexts`.

- [ ] **Step 3: Implement optional context output**

Modifier la signature et la construction du resultat dans `rag.py` :

```python
def answer_question(
    question: str,
    retriever: Any,
    chat_model: Any,
    *,
    include_contexts: bool = False,
) -> dict[str, Any]:
    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("A non-empty question is required.")

    documents = list(retriever.invoke(cleaned_question))
    sources = build_source_entries(documents)
    if not documents:
        result = {
            "question": cleaned_question,
            "answer": "Je ne sais pas, car aucun evenement pertinent n'a ete retrouve dans l'index.",
            "sources": [],
            "retrieved_chunk_count": 0,
        }
        if include_contexts:
            result["retrieved_contexts"] = []
        return result

    prompt = build_prompt()
    messages = prompt.invoke({
        "question": cleaned_question,
        "context": format_documents_for_prompt(documents),
    })
    response = chat_model.invoke(messages)
    result = {
        "question": cleaned_question,
        "answer": _coerce_response_text(response),
        "sources": [asdict(source) for source in sources],
        "retrieved_chunk_count": len(documents),
    }
    if include_contexts:
        result["retrieved_contexts"] = [
            document.page_content.strip()
            for document in documents
            if document.page_content.strip()
        ]
    return result
```

Appliquer la meme cle conditionnelle au retour sans document avec une liste vide.

Ajouter dans `service.py` :

```python
def ask_for_evaluation(self, question: str) -> dict[str, Any]:
    retriever, chat_model = self._ensure_runtime()
    return answer_question(
        question=question,
        retriever=retriever,
        chat_model=chat_model,
        include_contexts=True,
    )
```

- [ ] **Step 4: Verify the RAG and API tests**

Run:

```bash
conda run -n openagenda-rag env PYTHONNOUSERSITE=1 \
  python -m pytest -q tests/test_rag.py tests/test_api.py
```

Expected: all tests PASS and `/ask` still omits `retrieved_contexts`.

- [ ] **Step 5: Commit**

```bash
git add src/openagenda_rag/rag.py src/openagenda_rag/service.py \
  tests/test_rag.py tests/test_api.py
git commit -m "feat: expose retrieved contexts for evaluation"
```

### Task 2: Implementer l'evaluation RAGAS reelle

**Files:**
- Modify: `requirements.txt`
- Modify: `environment.yml`
- Create: `src/openagenda_rag/ragas_evaluation.py`
- Create: `scripts/evaluate_ragas.py`
- Create: `tests/fixtures/ragas_eval_dataset.csv`
- Create: `tests/test_ragas_evaluation.py`

- [ ] **Step 1: Add the three factual references**

Creer `tests/fixtures/ragas_eval_dataset.csv` :

```csv
case_id,question,reference,notes
concert_fishers,"Parle-moi de Concert Fishers a Paris","Concert Fishers est un concert de reprises pop, rock et funk organise le 21 juin 2026 a 19 h 30 au Gymnase Montparnasse a Paris dans le cadre de la Fete de la musique 2026.","cas nominal precis"
salon_photo,"Parle-moi de SALON DE LA PHOTO a Paris","Le SALON DE LA PHOTO est un evenement parisien consacre a la photographie. La reponse doit reprendre uniquement la date, le lieu et le lien presents dans le contexte OpenAgenda recupere.","cas nominal precis"
sortie_famille,"Je cherche une sortie en famille a Paris avec une visite theatricalisee","Le corpus propose notamment une visite theatralisee en famille dans le Marais et une visite des Passages Couverts. La reponse doit citer les propositions effectivement retrouvees et leurs informations pratiques.","cas agrege"
```

- [ ] **Step 2: Write failing unit tests for sample construction and score serialization**

Creer `tests/test_ragas_evaluation.py` avec des doubles reseau-off :

```python
from pathlib import Path

import pandas as pd
import pytest

from openagenda_rag.ragas_evaluation import (
    RagasCase,
    build_evaluation_rows,
    interpret_score,
    load_ragas_cases,
    summarize_ragas_scores,
)


def test_load_ragas_cases_requires_three_non_empty_cases(tmp_path: Path):
    path = tmp_path / "cases.csv"
    path.write_text(
        "case_id,question,reference,notes\n"
        "a,Question A,Reference A,note\n"
        "b,Question B,Reference B,note\n"
        "c,Question C,Reference C,note\n",
        encoding="utf-8",
    )

    cases = load_ragas_cases(path)

    assert [case.case_id for case in cases] == ["a", "b", "c"]


def test_build_evaluation_rows_keeps_question_context_response_reference():
    cases = [RagasCase("a", "Question A", "Reference A", "note")]

    rows = build_evaluation_rows(
        cases,
        responder=lambda _: {
            "answer": "Reponse A",
            "retrieved_contexts": ["Contexte A"],
            "sources": [{"title": "Evenement A"}],
        },
    )

    assert rows == [{
        "case_id": "a",
        "user_input": "Question A",
        "retrieved_contexts": ["Contexte A"],
        "response": "Reponse A",
        "reference": "Reference A",
        "source_titles": ["Evenement A"],
        "notes": "note",
    }]


def test_summarize_ragas_scores_computes_metric_means():
    frame = pd.DataFrame([
        {"faithfulness": 1.0, "answer_relevancy": 0.8},
        {"faithfulness": 0.5, "answer_relevancy": 0.6},
    ])

    summary = summarize_ragas_scores(frame, ["faithfulness", "answer_relevancy"])

    assert summary == {
        "example_count": 2,
        "metric_means": {"faithfulness": 0.75, "answer_relevancy": 0.7},
    }


@pytest.mark.parametrize(
    ("score", "expected"),
    [(0.85, "fort"), (0.65, "acceptable"), (0.4, "a ameliorer")],
)
def test_interpret_score_uses_documented_thresholds(score, expected):
    assert interpret_score(score) == expected
```

- [ ] **Step 3: Verify RED**

Run:

```bash
conda run -n openagenda-rag env PYTHONNOUSERSITE=1 \
  python -m pytest -q tests/test_ragas_evaluation.py
```

Expected: FAIL with `ModuleNotFoundError: openagenda_rag.ragas_evaluation`.

- [ ] **Step 4: Add pinned dependencies**

Ajouter dans `requirements.txt` :

```text
python-docx==1.2.0
ragas==0.4.3
```

Ajouter a `environment.yml` :

```yaml
  - pip:
      - -r requirements.txt
```

Cette section fait de `environment.yml` le point d'entree complet tout en
conservant `requirements.txt` comme liste pip utilisee par Docker.

- [ ] **Step 5: Implement the RAGAS module**

Creer `src/openagenda_rag/ragas_evaluation.py` avec :

```python
from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import json
from pathlib import Path
from typing import Any, Callable

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
    if not path.exists():
        raise FileNotFoundError(f"RAGAS dataset not found at {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    cases = [
        RagasCase(
            case_id=(row.get("case_id") or "").strip(),
            question=(row.get("question") or "").strip(),
            reference=(row.get("reference") or "").strip(),
            notes=(row.get("notes") or "").strip(),
        )
        for row in rows
        if (row.get("case_id") or "").strip()
        and (row.get("question") or "").strip()
        and (row.get("reference") or "").strip()
    ]
    if len(cases) < 3:
        raise ValueError("At least three complete RAGAS cases are required.")
    return cases


def build_evaluation_rows(
    cases: list[RagasCase],
    responder: Callable[[str], dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for case in cases:
        payload = responder(case.question)
        contexts = [
            str(value).strip()
            for value in payload.get("retrieved_contexts", [])
            if str(value).strip()
        ]
        response = str(payload.get("answer") or "").strip()
        if not contexts or not response:
            raise ValueError(f"Case {case.case_id!r} has an empty response or context.")
        rows.append({
            "case_id": case.case_id,
            "user_input": case.question,
            "retrieved_contexts": contexts,
            "response": response,
            "reference": case.reference,
            "source_titles": [
                str(source.get("title")).strip()
                for source in payload.get("sources", [])
                if str(source.get("title") or "").strip()
            ],
            "notes": case.notes,
        })
    return rows


def interpret_score(score: float) -> str:
    if score >= 0.8:
        return "fort"
    if score >= 0.6:
        return "acceptable"
    return "a ameliorer"


def summarize_ragas_scores(frame: pd.DataFrame, metric_names: list[str]) -> dict[str, Any]:
    return {
        "example_count": len(frame),
        "metric_means": {
            name: round(float(frame[name].dropna().mean()), 4)
            for name in metric_names
            if name in frame and not frame[name].dropna().empty
        },
    }
```

Ajouter une fonction `run_ragas` qui importe paresseusement :

```python
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings
from ragas import EvaluationDataset, evaluate
from ragas.dataset_schema import SingleTurnSample
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    AnswerCorrectness,
    AnswerRelevancy,
    ContextPrecision,
    Faithfulness,
)
```

Elle doit :

1. creer un `SingleTurnSample` par ligne ;
2. envelopper `ChatMistralAI(model="mistral-small-latest", temperature=0)` ;
3. envelopper `MistralAIEmbeddings(model="mistral-embed")` ;
4. executer `evaluate` avec les quatre metriques ;
5. joindre les scores aux lignes sources par ordre stable ;
6. ajouter une interpretation par metrique ;
7. ecrire un JSON detaille et un CSV lisible.

Si `AnswerCorrectness` n'est plus exporte par Ragas 0.4.3, utiliser
`FactualCorrectness` et nommer explicitement la colonne
`factual_correctness` dans le JSON, le rapport et le deck. Ne jamais renommer
un score de maniere trompeuse.

- [ ] **Step 6: Implement the CLI**

Creer `scripts/evaluate_ragas.py` avec les options :

```text
--dataset-path tests/fixtures/ragas_eval_dataset.csv
--output-json outputs/evaluation/ragas_results.json
--output-csv outputs/evaluation/ragas_examples.csv
--chat-model mistral-small-latest
--embedding-model mistral-embed
```

La CLI charge `.env`, refuse une cle absente, construit
`OpenAgendaRAGService.from_env()`, utilise `service.ask_for_evaluation` et
affiche le resume agrege.

- [ ] **Step 7: Verify GREEN and dependency integrity**

Run:

```bash
conda run -n openagenda-rag env PYTHONNOUSERSITE=1 \
  python -m pip install --no-user -r requirements.txt
conda run -n openagenda-rag env PYTHONNOUSERSITE=1 \
  python -m pytest -q tests/test_ragas_evaluation.py
conda run -n openagenda-rag env PYTHONNOUSERSITE=1 \
  python -m pip check
```

Expected: tests PASS and `No broken requirements found`.

- [ ] **Step 8: Run the real three-case RAGAS evaluation**

Run:

```bash
conda run -n openagenda-rag env PYTHONNOUSERSITE=1 \
  python scripts/evaluate_ragas.py
```

Expected:

- three detailed rows in `outputs/evaluation/ragas_results.json`;
- three rows in `outputs/evaluation/ragas_examples.csv`;
- no empty question, context, response or metric value;
- real metric means printed to the console.

- [ ] **Step 9: Commit**

```bash
git add requirements.txt environment.yml \
  src/openagenda_rag/ragas_evaluation.py scripts/evaluate_ragas.py \
  tests/fixtures/ragas_eval_dataset.csv tests/test_ragas_evaluation.py \
  outputs/evaluation/ragas_results.json outputs/evaluation/ragas_examples.csv
git commit -m "feat: add real Mistral-backed RAGAS evaluation"
```

### Task 3: Creer et chronometrer la demonstration API

**Files:**
- Create: `src/openagenda_rag/demo.py`
- Create: `scripts/demo_api_5min.py`
- Create: `scripts/demo_api_5min.sh`
- Create: `tests/test_demo.py`
- Create: `outputs/demo/demo_api_timing.json`

- [ ] **Step 1: Write failing tests**

Creer `tests/test_demo.py` :

```python
from openagenda_rag.demo import DemoScenario, run_demo


class FakeClient:
    def get(self, path):
        return FakeResponse(200, {"status": "ok"})

    def post(self, path, json):
        answer = (
            "Concert Fishers a Paris."
            if "Fishers" in json["question"]
            else "Je ne sais pas, le corpus est limite a Paris."
        )
        return FakeResponse(200, {"answer": answer, "sources": []})


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)

    def json(self):
        return self._payload


def test_run_demo_executes_nominal_and_edge_cases_under_limit():
    clock = iter([10.0, 42.0])
    result = run_demo(
        client=FakeClient(),
        scenarios=[
            DemoScenario("nominal", "Parle-moi de Concert Fishers a Paris"),
            DemoScenario("limite", "Quelles expositions photo a Lyon ?"),
        ],
        max_seconds=300,
        monotonic=lambda: next(clock),
    )

    assert result["duration_seconds"] == 32.0
    assert [item["case_id"] for item in result["scenarios"]] == ["nominal", "limite"]
    assert result["within_limit"] is True


def test_run_demo_marks_duration_over_five_minutes():
    clock = iter([0.0, 301.0])
    result = run_demo(
        client=FakeClient(),
        scenarios=[DemoScenario("nominal", "Question")],
        max_seconds=300,
        monotonic=lambda: next(clock),
    )

    assert result["within_limit"] is False
```

- [ ] **Step 2: Verify RED**

Run:

```bash
conda run -n openagenda-rag env PYTHONNOUSERSITE=1 \
  python -m pytest -q tests/test_demo.py
```

Expected: FAIL with `ModuleNotFoundError: openagenda_rag.demo`.

- [ ] **Step 3: Implement the timed demo**

Creer `src/openagenda_rag/demo.py` avec :

```python
from dataclasses import asdict, dataclass
from time import monotonic
from typing import Any, Callable


@dataclass(frozen=True)
class DemoScenario:
    case_id: str
    question: str


def run_demo(
    client: Any,
    scenarios: list[DemoScenario],
    max_seconds: float = 300.0,
    monotonic: Callable[[], float] = monotonic,
) -> dict[str, Any]:
    health = client.get("/health")
    health.raise_for_status()
    started = monotonic()
    results = []
    for scenario in scenarios:
        response = client.post("/ask", json={"question": scenario.question})
        response.raise_for_status()
        payload = response.json()
        results.append({
            **asdict(scenario),
            "answer": str(payload.get("answer") or ""),
            "sources": payload.get("sources", []),
        })
    duration = round(monotonic() - started, 3)
    return {
        "duration_seconds": duration,
        "max_seconds": max_seconds,
        "within_limit": duration < max_seconds,
        "scenarios": results,
    }
```

Creer `scripts/demo_api_5min.py` pour utiliser `httpx.Client`, ecrire
`outputs/demo/demo_api_timing.json`, afficher les deux reponses et retourner
`1` lorsque `within_limit` vaut `False`.

Creer `scripts/demo_api_5min.sh` :

```bash
#!/usr/bin/env bash
set -euo pipefail
python scripts/demo_api_5min.py "$@"
```

- [ ] **Step 4: Verify GREEN**

Run:

```bash
conda run -n openagenda-rag env PYTHONNOUSERSITE=1 \
  python -m pytest -q tests/test_demo.py
```

Expected: 2 tests PASS.

- [ ] **Step 5: Run the real Docker demo**

Run:

```bash
docker compose up -d
conda run -n openagenda-rag env PYTHONNOUSERSITE=1 \
  python scripts/demo_api_5min.py
```

Expected: HTTP success for the nominal and edge cases, `within_limit: true`,
and a measured duration below 300 seconds.

- [ ] **Step 6: Commit**

```bash
git add src/openagenda_rag/demo.py scripts/demo_api_5min.py \
  scripts/demo_api_5min.sh tests/test_demo.py \
  outputs/demo/demo_api_timing.json
git commit -m "feat: add five-minute API demonstration"
```

### Task 4: Rediger les supports de soutenance

**Files:**
- Create: `docs/soutenance/script_soutenance_15min.md`
- Create: `docs/soutenance/questions_reponses.md`

- [ ] **Step 1: Write the 15-minute speaking script**

Creer `docs/soutenance/script_soutenance_15min.md` avec un tableau de temps
dont la somme vaut exactement `15:00` :

```text
Slides 1-2  : 01:40
Slide 3     : 00:50
Slides 4-6  : 02:40
Slides 7-9  : 02:30
Slide 10    : 03:30
Slides 11-13: 02:20
Slides 14-15: 01:30
Total       : 15:00
```

Sous chaque plage, ecrire le texte oral complet et les actions a l'ecran.
Inclure l'explication de l'erreur `dquote>` comme exemple de diagnostic shell,
sans la reproduire volontairement pendant la demonstration.

- [ ] **Step 2: Write at least twelve prepared answers**

Creer `docs/soutenance/questions_reponses.md` avec des reponses de 30 a 60
secondes aux questions exactes :

1. Pourquoi un RAG plutot qu'un LLM seul ?
2. Pourquoi avoir choisi FAISS ?
3. Pourquoi `mistral-embed` ?
4. Pourquoi `mistral-small-latest` ?
5. Pourquoi limiter le POC a Paris ?
6. Comment les textes sont-ils decoupes ?
7. Comment evitez-vous les hallucinations ?
8. Pourquoi quatre chunks sont-ils recuperes ?
9. Que mesurent les scores RAGAS ?
10. Pourquoi la demonstration depend-elle d'Internet ?
11. Comment proteger `/rebuild` ?
12. Comment passer a plusieurs villes et a la production ?
13. Quel est le cout principal du systeme ?
14. Que se passe-t-il si aucune source n'est pertinente ?

- [ ] **Step 3: Verify timing and question count**

Run:

```bash
rg -n "^## Question" docs/soutenance/questions_reponses.md | wc -l
rg -n "Total.*15:00" docs/soutenance/script_soutenance_15min.md
```

Expected: at least 12 questions and one exact `Total: 15:00`.

- [ ] **Step 4: Commit**

```bash
git add docs/soutenance/script_soutenance_15min.md \
  docs/soutenance/questions_reponses.md
git commit -m "docs: add timed soutenance script and jury answers"
```

### Task 5: Generer le rapport technique depuis le modele

**Files:**
- Create: `scripts/build_report.py`
- Create: `outputs/rapport-technique-openagenda-rag.docx`
- Source: `/home/hgbe/Téléchargements/Template+de+rapport+technique (1).docx`

- [ ] **Step 1: Implement a reproducible report builder**

Creer `scripts/build_report.py` avec `python-docx`. Le script doit :

1. charger le modele avec `Document(template_path)` ;
2. conserver le titre et les dix rubriques ;
3. remplacer chaque liste d'instructions par le contenu reel du projet ;
4. ajouter une table RAGAS a six colonnes :
   `Question`, `Contexte`, `Reponse`, `Scores`, `Interpretation`, `Sources` ;
5. lire `data/processed/fetch_manifest.json`,
   `data/index/index_manifest.json`,
   `outputs/evaluation/ragas_results.json` et
   `outputs/demo/demo_api_timing.json` ;
6. inserer les valeurs reelles plutot que des constantes ;
7. ajouter les commandes de reproduction en annexe ;
8. enregistrer `outputs/rapport-technique-openagenda-rag.docx`.

Le script doit appliquer :

```python
from docx import Document
from docx.shared import Cm, Pt

document = Document(template_path)
for section in document.sections:
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)

styles = document.styles
styles["Normal"].font.name = "Aptos"
styles["Normal"].font.size = Pt(10.5)
```

Les tableaux utilisent des largeurs explicites et des en-tetes repetes. Les
listes utilisent les styles Word `List Bullet` et `List Number`, jamais des
caracteres de puce saisis manuellement.

- [ ] **Step 2: Generate the report**

Run:

```bash
conda run -n openagenda-rag env PYTHONNOUSERSITE=1 \
  python scripts/build_report.py \
  --template-path "/home/hgbe/Téléchargements/Template+de+rapport+technique (1).docx" \
  --output-path outputs/rapport-technique-openagenda-rag.docx
```

Expected: a non-empty DOCX containing all ten headings and three RAGAS rows.

- [ ] **Step 3: Render and inspect every page**

Run the packaged renderer from the document skill. If its Python environment
still lacks `pdf2image`, use LibreOffice with an isolated profile, then
`pdftoppm`.

Expected:

- every page has a PNG;
- no clipped headings, tables or code blocks;
- no empty template instruction remains;
- page breaks keep headings with their first paragraph.

- [ ] **Step 4: Run structural audits**

Run:

```bash
unzip -p outputs/rapport-technique-openagenda-rag.docx word/document.xml \
  | rg "Objectifs du projet|Architecture du systeme|Evaluation du systeme|Annexes"
```

Expected: all required sections found.

- [ ] **Step 5: Commit**

```bash
git add scripts/build_report.py outputs/rapport-technique-openagenda-rag.docx
git commit -m "docs: add completed technical report"
```

### Task 6: Mettre a jour le deck de quinze slides

**Files:**
- Modify: `outputs/openagenda-rag-soutenance.pptx`
- Modify: `outputs/openagenda-rag-soutenance.pptx.inspect.ndjson`

- [ ] **Step 1: Prepare the external presentation workspace**

Use the existing PPTX as the only visual reference. Create the scratch
workspace outside the repository and run:

```bash
node "$SKILL_DIR/template_following_scripts/inspect_template_deck.mjs" \
  --workspace "$TMP_DIR" \
  --pptx "/home/hgbe/openclassrooms/Projet7/outputs/openagenda-rag-soutenance.pptx"
```

Create and validate a frame map preserving all fifteen source slides.

- [ ] **Step 2: Replace the narrative with measured RAGAS content**

Use `@oai/artifact-tool` from a plain `.mjs` module. Preserve the current
typography, palette, footer and slide numbering.

Set the final slide jobs exactly:

1. contexte Puls-Events ;
2. besoin metier ;
3. fonctionnement simple du RAG ;
4. corpus Paris et fenetre temporelle ;
5. pipeline complet ;
6. qualite et preparation des donnees ;
7. chunking, Mistral embeddings et FAISS ;
8. chatbot, prompt et garde-fous ;
9. FastAPI, Docker et securite ;
10. protocole de demo nominal + limite sous cinq minutes ;
11. methode RAGAS et definition des quatre metriques ;
12. cas RAGAS Concert Fishers et Salon de la Photo ;
13. cas RAGAS famille, moyennes mesurees et interpretation ;
14. limites techniques, metier et evaluation ;
15. priorites d'amelioration et conclusion.

Les slides 12 et 13 doivent lire
`outputs/evaluation/ragas_results.json`; aucun score ne doit etre saisi a la
main.

- [ ] **Step 3: Export and inspect**

Export to:

```text
outputs/openagenda-rag-soutenance.pptx
```

Render all slides, create a contact sheet and inspect every slide at full size.
Fix:

- text wrapping in one-line titles ;
- body text below 16 pt ;
- overlaps and clipping ;
- repeated generic card layouts ;
- mismatch between score labels and JSON.

- [ ] **Step 4: Verify slide count and content**

Run:

```bash
unzip -l outputs/openagenda-rag-soutenance.pptx \
  | rg "ppt/slides/slide[0-9]+\\.xml" | wc -l
rg -n "RAGAS|faithfulness|context_precision|demo" \
  outputs/openagenda-rag-soutenance.pptx.inspect.ndjson
```

Expected: exactly 15 slides and all required concepts present.

- [ ] **Step 5: Commit**

```bash
git add outputs/openagenda-rag-soutenance.pptx \
  outputs/openagenda-rag-soutenance.pptx.inspect.ndjson
git commit -m "docs: update soutenance deck with RAGAS results"
```

### Task 7: Documenter et verifier le livrable complet

**Files:**
- Modify: `README.md`
- Test: all tests

- [ ] **Step 1: Update the README**

Documenter :

```bash
python scripts/evaluate_ragas.py
bash scripts/demo_api_5min.sh
python scripts/build_report.py \
  --template-path "/home/hgbe/Téléchargements/Template+de+rapport+technique (1).docx"
```

Ajouter :

- les quatre metriques RAGAS et leur interpretation ;
- le chemin du JSON et du CSV ;
- la duree mesuree de la demonstration ;
- les liens vers le rapport, le deck, le script oral et les questions ;
- la limite liee au compte Mistral gratuit.

Preserver les modifications utilisateur deja presentes dans `README.md` et
integrer les nouvelles sections sans les ecraser.

- [ ] **Step 2: Run the full test suite**

Run:

```bash
conda run -n openagenda-rag env PYTHONNOUSERSITE=1 \
  python -m pytest -q
```

Expected: all tests PASS.

- [ ] **Step 3: Verify environment and imports**

Run:

```bash
conda run -n openagenda-rag env PYTHONNOUSERSITE=1 \
  python scripts/check_env.py
conda run -n openagenda-rag env PYTHONNOUSERSITE=1 \
  python -m pip check
```

Expected: imports pass, Mistral embedding is non-empty, no broken requirements.

- [ ] **Step 4: Verify all acceptance artifacts**

Run:

```bash
test -s outputs/evaluation/ragas_results.json
test -s outputs/evaluation/ragas_examples.csv
test -s outputs/demo/demo_api_timing.json
test -s outputs/rapport-technique-openagenda-rag.docx
test -s outputs/openagenda-rag-soutenance.pptx
test -s docs/soutenance/script_soutenance_15min.md
test -s docs/soutenance/questions_reponses.md
```

Expected: exit code 0.

- [ ] **Step 5: Confirm cross-artifact consistency**

Compare:

- example count and scores between RAGAS JSON, CSV, report and slides ;
- event count and chunk count between manifests, report and slides ;
- demonstration duration between timing JSON, README, report and slide 10 ;
- model names between `.env.example`, code, README, report and slides.

Expected: no mismatch.

- [ ] **Step 6: Commit**

```bash
git add README.md
git commit -m "docs: document RAGAS evaluation and final demonstration"
```

- [ ] **Step 7: Request final code review**

Use `superpowers:requesting-code-review` against the implementation commits.
Fix every Critical and Important finding, rerun the full verification, then
prepare the final handoff.
