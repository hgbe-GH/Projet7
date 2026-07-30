# Guide HTML de soutenance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produire un guide HTML autonome, à la première personne, qui permet de présenter le POC RAG en 15 minutes et de répondre aux questions du jury.

**Architecture:** Un unique fichier `outputs/guide-soutenance-openagenda-rag.html` contient le style, le conducteur oral, les notes candidat, les commandes de démonstration et le jury blanc. Aucun script, framework ou chargement réseau n'est nécessaire. Les contrôles utilisent uniquement le parseur HTML de Python, la recherche textuelle et une inspection dans un navigateur local.

**Tech Stack:** HTML5, CSS embarqué, liens et ancres relatifs, Python standard library pour la validation, navigateur local pour l'inspection.

---

### Task 1: Construire le guide autonome

**Files:**
- Create: `outputs/guide-soutenance-openagenda-rag.html`
- Reference: `docs/superpowers/specs/2026-07-30-guide-soutenance-html-design.md`
- Reference: `docs/soutenance/script_soutenance_15min.md`
- Reference: `docs/soutenance/questions_reponses.md`
- Reference: `README.md`

- [ ] **Step 1: Créer la structure HTML**

Créer un document HTML5 en français avec :

```html
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Guide de soutenance - Assistant RAG OpenAgenda</title>
</head>
<body>
  <header id="top"></header>
  <nav aria-label="Navigation du guide"></nav>
  <main>
    <section id="urgence"></section>
    <section id="conducteur"></section>
    <section id="demo"></section>
    <section id="rapport-depot"></section>
    <section id="notions"></section>
    <section id="jury"></section>
    <section id="secours"></section>
    <section id="final"></section>
  </main>
</body>
</html>
```

Le CSS embarqué doit fournir une largeur de lecture maximale de 1180 px, une navigation fixe, des blocs visuellement distincts pour le discours, les actions, les notes et les alertes, une grille responsive et un mode impression sans navigation fixe.

- [ ] **Step 2: Rédiger le conducteur complet**

Rédiger à la première personne les 15 étapes du PowerPoint. Pour chaque étape, inclure :

```html
<article class="step">
  <div class="step-heading">
    <span class="time">00:00-00:45</span>
    <h3>Slide 1 - Contexte et objectif</h3>
  </div>
  <section class="say"><h4>Ce que je dis</h4></section>
  <section class="do"><h4>Ce que je fais</h4></section>
  <details class="notes"><summary>Ce que je dois comprendre</summary></details>
  <p class="transition"><strong>Transition :</strong> ...</p>
</article>
```

Le conducteur doit couvrir explicitement la démo, le rapport et le dépôt dans une durée cible de 12 à 15 minutes.

- [ ] **Step 3: Ajouter les explications et le jury blanc**

Inclure les notions RAG, embeddings, chunks, FAISS, `top_k`, FastAPI, Docker et RAGAS. Ajouter des réponses directes et argumentées sur les cinq axes officiels :

- modèles et architecture ;
- données et qualité des embeddings ;
- évaluation des performances ;
- limites ;
- reproductibilité, industrialisation et usage métier.

Ajouter les questions sensibles propres au projet : fenêtre 2025-07-10/2026-07-10, instantané figé, 4 tests annotés contre 3 cas RAGAS, `top_k=4`, chunks 1000/200, dépendance Mistral, absence de seuil de similarité, sécurité de `/rebuild` et faiblesse statistique des trois cas.

- [ ] **Step 4: Ajouter les commandes sûres**

Inclure sans valeur secrète :

```bash
conda activate openagenda-rag
docker compose up -d
docker compose ps
curl http://localhost:8000/health
bash scripts/demo_api_5min.sh
```

Ajouter les liens relatifs :

```html
<a href="openagenda-rag-soutenance.pptx">PowerPoint</a>
<a href="rapport-technique-openagenda-rag.pdf">Rapport PDF</a>
```

- [ ] **Step 5: Enregistrer l'artefact**

```bash
git add -f outputs/guide-soutenance-openagenda-rag.html
git commit -m "docs: add complete soutenance reading guide"
```

Expected: le commit contient uniquement le guide HTML.

### Task 2: Vérifier le fond et la structure

**Files:**
- Test: `outputs/guide-soutenance-openagenda-rag.html`

- [ ] **Step 1: Valider le HTML et les sections obligatoires**

Run:

```bash
python - <<'PY'
from html.parser import HTMLParser
from pathlib import Path

path = Path("outputs/guide-soutenance-openagenda-rag.html")
text = path.read_text(encoding="utf-8")
HTMLParser().feed(text)
required = [
    'id="urgence"', 'id="conducteur"', 'id="demo"',
    'id="rapport-depot"', 'id="notions"', 'id="jury"',
    'id="secours"', 'id="final"', "Ce que je dis",
    "Ce que je fais", "Ce que je dois comprendre",
    "59 tests", "7 586", "14 903", "0,683",
]
missing = [item for item in required if item not in text]
assert not missing, missing
assert text.count('class="step"') >= 15
print("HTML structure and required content: OK")
PY
```

Expected: `HTML structure and required content: OK`.

- [ ] **Step 2: Rechercher les erreurs de livraison**

Run:

```bash
rg -n 'TBD|TODO|PLACEHOLDER|Lorem ipsum|MISTRAL_API_KEY=' outputs/guide-soutenance-openagenda-rag.html
```

Expected: aucune sortie.

- [ ] **Step 3: Vérifier les liens locaux**

Run:

```bash
test -f outputs/openagenda-rag-soutenance.pptx
test -f outputs/rapport-technique-openagenda-rag.pdf
```

Expected: code de sortie 0.

### Task 3: Vérifier le rendu et livrer

**Files:**
- Inspect: `outputs/guide-soutenance-openagenda-rag.html`

- [ ] **Step 1: Ouvrir le document dans un navigateur local**

Ouvrir l'URL `file:///home/hgbe/openclassrooms/Projet7/outputs/guide-soutenance-openagenda-rag.html` et inspecter le haut de page, le conducteur, le jury blanc et le mode mobile.

- [ ] **Step 2: Contrôler la lisibilité**

Vérifier l'absence de chevauchement, de texte coupé, de défilement horizontal, de contraste insuffisant et de commandes illisibles. Vérifier que la navigation mène aux huit sections.

- [ ] **Step 3: Exécuter la vérification finale du projet**

Run:

```bash
conda run -n openagenda-rag env PYTHONNOUSERSITE=1 python -m pytest -q
docker compose ps
curl -fsS http://localhost:8000/health
```

Expected: `59 passed`, conteneur `healthy`, réponse JSON avec `"status":"ok"`.

- [ ] **Step 4: Vérifier l'état Git**

Run:

```bash
git status --short
git log -2 --oneline
```

Expected: aucun changement non enregistré et présence du commit du guide.
