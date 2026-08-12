# Refonte visuelle de la soutenance RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produire une version plus visuelle et plus lisible du PowerPoint de soutenance, sans modifier les faits, le périmètre ni le script de démonstration.

**Architecture:** Le fichier PowerPoint existant est le gabarit. La refonte remplace uniquement le contenu des éléments hérités avec artifact-tool : elle conserve la palette et le chrome du deck, mais varie les compositions entre comparaison, flux, zoom de données, visualisation de métriques et feuille de route. Les explications détaillées restent dans les notes et le guide HTML.

**Tech Stack:** PowerPoint, `@oai/artifact-tool`, scripts de validation du skill Presentations, Docker Compose, pytest.

---

### Task 1: Préparer une version visuelle conforme au gabarit

**Files:**
- Modify: `outputs/openagenda-rag-soutenance.pptx`
- Modify: `outputs/openagenda-rag-soutenance.pptx.inspect.ndjson`
- Create: `/tmp/codex-presentations/reprise-soutenance-15min/tmp/build-reprise-visuelle.mjs`

- [ ] **Step 1: Reprendre le deck comme gabarit strict**

  Utiliser `outputs/openagenda-rag-soutenance.pptx` comme source, l’inspecter entièrement et reconstruire un starter avec le plan de correspondance déjà présent dans `/tmp/codex-presentations/reprise-soutenance-15min/tmp/template-frame-map.json`.

- [ ] **Step 2: Remplacer les compositions répétitives par une visualisation principale par slide**

  Mettre à jour les 12 slides en gardant exactement les preuves suivantes :

  ```text
  7 586 événements · 14 903 passages · 59 tests
  CHIMERE : 10 273 caractères · chunks 1 000 / overlap 200
  mistral-embed · mistral-small-latest · top_k=4
  RAGAS : 0,900 · 0,846 · 1,000 · 0,683
  ```

  Utiliser : une comparaison sur slide 2, une transformation de données sur slide 3,
  un zoom CHIMERE sur slide 4, un flux RAG sur slides 5–6, un contrat API sur slide 7,
  une séquence de démo sur slide 8, une pyramide de contrôle sur slide 9, une lecture
  de métriques sur slide 10, une matrice limite/action sur slide 11 et une feuille de
  route sur slide 12.

- [ ] **Step 3: Conserver les notes présentateur**

  Préserver ou adapter les notes afin que le conducteur reste autour de 14 min 35, avec
  une démonstration terminal de deux minutes et quarante secondes maximum pour rapport/dépôt.

- [ ] **Step 4: Exporter le deck et son inspection**

  Exécuter le module avec artifact-tool, qui écrit :

  ```bash
  node /tmp/codex-presentations/reprise-soutenance-15min/tmp/build-reprise-visuelle.mjs
  ```

  Résultat attendu : `outputs/openagenda-rag-soutenance.pptx` contient 12 slides et 12 notes présentateur.

- [ ] **Step 5: Commit**

  ```bash
  git add -f outputs/openagenda-rag-soutenance.pptx outputs/openagenda-rag-soutenance.pptx.inspect.ndjson
  git commit -m "docs: rendre la soutenance plus visuelle"
  ```

### Task 2: Vérifier la lecture et la fidélité du PowerPoint

**Files:**
- Verify: `outputs/openagenda-rag-soutenance.pptx`

- [ ] **Step 1: Rendre toutes les slides et vérifier les débordements**

  ```bash
  python /home/hgbe/.codex/plugins/cache/openai-primary-runtime/presentations/26.630.12135/skills/presentations/container_tools/render_slides.py outputs/openagenda-rag-soutenance.pptx --output_dir /tmp/codex-presentations/reprise-soutenance-15min/tmp/rendered-visual
  python /home/hgbe/.codex/plugins/cache/openai-primary-runtime/presentations/26.630.12135/skills/presentations/container_tools/slides_test.py outputs/openagenda-rag-soutenance.pptx
  ```

  Résultat attendu : aucune erreur d’overflow ; le montage confirme une hiérarchie lisible à distance.

- [ ] **Step 2: Contrôler la fidélité du gabarit**

  ```bash
  node /home/hgbe/.codex/plugins/cache/openai-primary-runtime/presentations/26.630.12135/skills/presentations/template_following_scripts/check_template_fidelity.mjs --workspace /tmp/codex-presentations/reprise-soutenance-15min/tmp --starter-pptx /tmp/codex-presentations/reprise-soutenance-15min/tmp/template-starter.pptx --final-pptx /home/hgbe/openclassrooms/Projet7/outputs/openagenda-rag-soutenance.pptx --map /tmp/codex-presentations/reprise-soutenance-15min/tmp/template-frame-map.json --starter-layout-dir /tmp/codex-presentations/reprise-soutenance-15min/tmp/template-starter-layout --final-layout-dir /tmp/codex-presentations/reprise-soutenance-15min/tmp/final-layout-visual --edit-dir /tmp/codex-presentations/reprise-soutenance-15min/tmp
  ```

  Résultat attendu : `status: pass` et zéro écart non autorisé.

### Task 3: Rejouer les preuves qui soutiennent la démo

**Files:**
- Verify: `scripts/demo_api_5min.sh`
- Verify: `outputs/demo/demo_api_timing.json`

- [ ] **Step 1: Rejouer la suite automatisée**

  ```bash
  conda run -n openagenda-rag env PYTHONNOUSERSITE=1 python -m pytest -q
  ```

  Résultat attendu : `59 passed`.

- [ ] **Step 2: Démarrer l’API et exécuter la démo terminal**

  ```bash
  docker compose up -d
  curl --fail http://localhost:8000/health
  bash scripts/demo_api_5min.sh
  ```

  Résultat attendu : un cas Paris avec quatre sources et un cas Lyon prudent, sans événement lyonnais inventé.

- [ ] **Step 3: Commit final si nécessaire**

  ```bash
  git status --short
  ```

  Résultat attendu : aucun fichier livré non versionné.

## Self-review

- Couverture : le plan couvre la direction visuelle, les 12 points narratifs, les notes, le rendu, la fidélité du gabarit, les tests et la démo.
- Placeholders : aucun TBD, TODO ou changement indéfini.
- Cohérence : les métriques et chiffres restent ceux validés dans le dépôt ; la CI/CD est présentée seulement comme une proposition.
