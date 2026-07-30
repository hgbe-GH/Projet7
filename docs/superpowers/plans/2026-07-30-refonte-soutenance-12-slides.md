# Refonte de la soutenance en 12 slides Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer la présentation de 15 slides par un deck de 12 slides plus simple et synchroniser le guide HTML avec des explications causales adaptées au candidat.

**Architecture:** Le PowerPoint existant sert de référence visuelle et de source de styles. Une reconstruction contrôlée avec `@oai/artifact-tool` produit 12 slides et des notes orateur cohérentes. Le guide HTML reste autonome mais remplace les 15 étapes par 12 fiches pédagogiques structurées en entrée, traitement, sortie, justification, discours et défense devant le jury.

**Tech Stack:** PowerPoint, `@oai/artifact-tool`, scripts de contrôle de la compétence Presentations, HTML5/CSS, Python standard library, Playwright CLI.

---

### Task 1: Écrire les contrôles de structure en échec attendu

**Files:**
- Create: `/tmp/projet7-refonte-soutenance-qa.py`
- Target: `outputs/openagenda-rag-soutenance.pptx`
- Target: `outputs/guide-soutenance-openagenda-rag.html`

- [ ] **Step 1: Créer le contrôle**

Le script doit :

```python
from html.parser import HTMLParser
from pathlib import Path
import zipfile

root = Path("/home/hgbe/openclassrooms/Projet7")
pptx = root / "outputs/openagenda-rag-soutenance.pptx"
html = root / "outputs/guide-soutenance-openagenda-rag.html"

with zipfile.ZipFile(pptx) as archive:
    slides = [
        name for name in archive.namelist()
        if name.startswith("ppt/slides/slide") and name.endswith(".xml")
    ]
assert len(slides) == 12, len(slides)

text = html.read_text(encoding="utf-8")
HTMLParser().feed(text)
assert text.count('class="step"') == 12
for heading in [
    "Ce que je cherche à démontrer",
    "Ce qui entre",
    "Ce que mon code fait",
    "Ce qui sort",
    "Pourquoi ce choix",
    "Ce que je dis",
    "Ce que je montre",
    "À ne pas dire",
    "Question probable",
]:
    assert text.count(heading) >= 12, heading
print("Deck 12 slides et guide synchronisé : OK")
```

- [ ] **Step 2: Exécuter le contrôle**

Run:

```bash
python /tmp/projet7-refonte-soutenance-qa.py
```

Expected: échec indiquant `15` slides ou `15` étapes.

### Task 2: Auditer le deck de référence et préparer la reconstruction

**Files:**
- Reference: `outputs/openagenda-rag-soutenance.pptx`
- Create in external scratch: `template-audit.txt`
- Create in external scratch: `template-frame-map.json`
- Create in external scratch: `deviation-log.txt`
- Create in external scratch: `template-starter.pptx`

- [ ] **Step 1: Créer un espace de travail externe**

Run:

```bash
scratch_root=$(node -p "require('node:os').tmpdir()")
workspace="$scratch_root/codex-presentations/projet7-refonte-12-slides"
mkdir -p "$workspace/tmp"
```

Expected: un dossier externe au dépôt.

- [ ] **Step 2: Inspecter le deck complet**

Run:

```bash
node "$SKILL_DIR/template_following_scripts/inspect_template_deck.mjs" \
  --workspace "$workspace/tmp" \
  --pptx "/home/hgbe/openclassrooms/Projet7/outputs/openagenda-rag-soutenance.pptx"
```

Expected: audit des 15 slides, aperçu et carte des objets.

- [ ] **Step 3: Mapper les 12 slides**

Le fichier `template-frame-map.json` doit conserver ces cadres sources :

```json
[
  {"sourceSlide": 1, "outputSlide": 1},
  {"sourceSlide": 2, "outputSlide": 2},
  {"sourceSlide": 3, "outputSlide": 3},
  {"sourceSlide": 4, "outputSlide": 4},
  {"sourceSlide": 5, "outputSlide": 5},
  {"sourceSlide": 6, "outputSlide": 6},
  {"sourceSlide": 7, "outputSlide": 7},
  {"sourceSlide": 9, "outputSlide": 8},
  {"sourceSlide": 11, "outputSlide": 9},
  {"sourceSlide": 13, "outputSlide": 10},
  {"sourceSlide": 14, "outputSlide": 11},
  {"sourceSlide": 15, "outputSlide": 12}
]
```

Les insertions de formes natives sont limitées aux schémas simples et aux repères de métriques. La palette, la typographie, les marges, les numéros de page et le pied de page sont conservés.

- [ ] **Step 4: Valider et préparer le starter**

Run:

```bash
node "$SKILL_DIR/template_following_scripts/validate_template_plan.mjs" \
  --workspace "$workspace/tmp" \
  --map "$workspace/tmp/template-frame-map.json"

node "$SKILL_DIR/template_following_scripts/prepare_template_starter_deck.mjs" \
  --workspace "$workspace/tmp" \
  --pptx "/home/hgbe/openclassrooms/Projet7/outputs/openagenda-rag-soutenance.pptx" \
  --map "$workspace/tmp/template-frame-map.json" \
  --out "$workspace/tmp/template-starter.pptx" \
  --preview-dir "$workspace/tmp/template-starter-preview" \
  --layout-dir "$workspace/tmp/template-starter-layout" \
  --contact-sheet "$workspace/tmp/template-starter-contact-sheet.png"
```

Expected: un starter de 12 slides validé.

### Task 3: Reconstruire le PowerPoint simplifié

**Files:**
- Create in external scratch: `build-soutenance-12-slides.mjs`
- Modify: `outputs/openagenda-rag-soutenance.pptx`
- Modify: `outputs/openagenda-rag-soutenance.pptx.inspect.ndjson`

- [ ] **Step 1: Initialiser artifact-tool**

Run:

```bash
node "$SKILL_DIR/container_tools/setup_artifact_tool_workspace.mjs" \
  --workspace "$workspace/tmp"
```

Expected: `@oai/artifact-tool` résolu depuis le workspace.

- [ ] **Step 2: Écrire le module de présentation**

Le module importe `template-starter.pptx`, remplace le contenu des 12 slides selon la spécification et ajoute des notes orateur. Il conserve le format 16:9, les couleurs et les styles du deck source. Les slides 3 et 5 utilisent des formes PowerPoint simples avec connecteurs créés avant les nœuds.

Le contenu visible est limité à :

- slide 1 : mission, message de faisabilité et trois preuves ;
- slide 2 : recherche par mots-clés, LLM seul, RAG ;
- slide 3 : question, FAISS, contexte, Mistral, sources ;
- slide 4 : source, fenêtre, volume, snapshot ;
- slide 5 : collecte, préparation, indexation, RAG, API, Docker ;
- slide 6 : chunks 1000/200, `mistral-embed`, 14 903 passages, métadonnées ;
- slide 7 : `top_k=4`, prompt contraint, endpoints, mémoire, Docker et secrets ;
- slide 8 : cas Paris, cas Lyon, durée, rapport et dépôt ;
- slide 9 : quatre cas fonctionnels, trois cas RAGAS, quatre métriques ;
- slide 10 : 0,900, 0,846, 1,000, 0,683 et leur interprétation ;
- slide 11 : cinq limites et leur impact ;
- slide 12 : données, garde-fous, industrialisation et recommandation.

- [ ] **Step 3: Exporter et inspecter**

Run:

```bash
node "$workspace/tmp/build-soutenance-12-slides.mjs"
python "$SKILL_DIR/container_tools/render_slides.py" \
  "/home/hgbe/openclassrooms/Projet7/outputs/openagenda-rag-soutenance.pptx"
python "$SKILL_DIR/container_tools/slides_test.py" \
  "/home/hgbe/openclassrooms/Projet7/outputs/openagenda-rag-soutenance.pptx"
```

Expected: 12 slides rendues, aucun débordement.

- [ ] **Step 4: Inspecter la planche contact**

Créer une planche contact et vérifier chaque titre, alignement, contraste, enchaînement et niveau de densité. Corriger toute collision ou ligne de titre imprévue avant de poursuivre.

### Task 4: Refaire le guide HTML autour de la compréhension

**Files:**
- Modify: `outputs/guide-soutenance-openagenda-rag.html`

- [ ] **Step 1: Remplacer le conducteur 15 slides par 12 fiches**

Chaque fiche utilise :

```html
<article class="step">
  <header class="step-heading"></header>
  <section class="intent"><h4>Ce que je cherche à démontrer</h4></section>
  <section class="flow-in"><h4>Ce qui entre</h4></section>
  <section class="process"><h4>Ce que mon code fait</h4></section>
  <section class="flow-out"><h4>Ce qui sort</h4></section>
  <section class="why"><h4>Pourquoi ce choix</h4></section>
  <section class="say"><h4>Ce que je dis</h4></section>
  <section class="do"><h4>Ce que je montre</h4></section>
  <section class="avoid"><h4>À ne pas dire</h4></section>
  <details class="likely-question"><summary>Question probable</summary></details>
</article>
```

- [ ] **Step 2: Synchroniser le minutage et les manipulations**

Le conducteur totalise 15 minutes :

- slides 1 à 3 : 3 minutes ;
- slides 4 à 7 : 5 minutes ;
- slide 8 et parcours rapport/dépôt : 2 minutes ;
- slides 9 à 10 : 2 minutes 30 ;
- slides 11 à 12 : 2 minutes 30.

La démonstration utilise `bash scripts/demo_api_5min.sh`. Le parcours montre le sommaire du rapport et les dossiers `scripts`, `src`, `tests` et `seed-data`.

- [ ] **Step 3: Conserver et réviser le jury blanc**

Les 32 questions existantes sont conservées. Les réponses sont alignées sur le nouveau PowerPoint, notamment pour le snapshot, les quatre cas fonctionnels, les trois cas RAGAS, le score de correction et la limite de production.

### Task 5: Vérifier, corriger et enregistrer

**Files:**
- Test: `/tmp/projet7-refonte-soutenance-qa.py`
- Verify: `outputs/openagenda-rag-soutenance.pptx`
- Verify: `outputs/guide-soutenance-openagenda-rag.html`

- [ ] **Step 1: Exécuter le contrôle structurel**

Run:

```bash
python /tmp/projet7-refonte-soutenance-qa.py
```

Expected: `Deck 12 slides et guide synchronisé : OK`.

- [ ] **Step 2: Inspecter le HTML dans un navigateur**

Servir `outputs/`, ouvrir le guide avec Playwright, vérifier desktop et mobile, les ancres, les fiches et une question repliable. La console doit contenir zéro erreur et la largeur mobile ne doit pas déborder.

- [ ] **Step 3: Vérifier le projet**

Run:

```bash
conda run -n openagenda-rag env PYTHONNOUSERSITE=1 python -m pytest -q
docker compose ps
curl -fsS http://localhost:8000/health
```

Expected: `59 passed`, conteneur `healthy`, JSON avec `"status":"ok"`.

- [ ] **Step 4: Vérifier les fichiers finaux**

Run:

```bash
git diff --check
git status --short
```

Expected: uniquement les fichiers de présentation et de guide attendus avant commit.

- [ ] **Step 5: Commit**

Run:

```bash
git add -f \
  outputs/openagenda-rag-soutenance.pptx \
  outputs/openagenda-rag-soutenance.pptx.inspect.ndjson \
  outputs/guide-soutenance-openagenda-rag.html
git commit -m "docs: simplify soutenance to 12 slides"
```

Expected: un commit contenant uniquement les supports de soutenance finaux.
