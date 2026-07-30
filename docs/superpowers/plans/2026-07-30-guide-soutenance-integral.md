# Guide intégral de soutenance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformer le guide HTML en un script oral intégral couvrant les 30 minutes de soutenance, tout en restant synchronisé avec les 12 slides.

**Architecture:** Le PowerPoint reste inchangé. Le fichier HTML autonome contient trois niveaux de lecture : le texte à prononcer, les actions à effectuer et les explications à consulter en cas de question. Un contrôle Python vérifie la présence des 12 fiches, des blocs pédagogiques, des séquences hors PowerPoint et des faits techniques obligatoires.

**Tech Stack:** HTML5, CSS responsive, Python standard library pour les contrôles, Playwright CLI pour la validation navigateur.

---

### Task 1: Étendre le contrôle automatique du guide

**Files:**
- Create: `/tmp/projet7-guide-integral-qa.py`
- Test: `outputs/guide-soutenance-openagenda-rag.html`

- [ ] **Step 1: Écrire le contrôle qui échoue sur le guide condensé**

```python
from html.parser import HTMLParser
from pathlib import Path

guide = Path("/home/hgbe/openclassrooms/Projet7/outputs/guide-soutenance-openagenda-rag.html")
text = guide.read_text(encoding="utf-8")
HTMLParser().feed(text)

assert text.count('class="step"') == 12
assert text.count('class="oral-script"') == 12
assert text.count("Version courte si je manque de temps") == 12
assert text.count("Réponse courte") >= 20
assert text.count("Si le jury insiste") >= 20

for section_id in [
    "avant-appel",
    "conducteur",
    "demo-live",
    "rapport-depot",
    "questions-jury",
    "plans-secours",
    "debrief",
]:
    assert f'id="{section_id}"' in text

for fact in [
    "7 586",
    "14 903",
    "59 tests",
    "top_k=4",
    "1000",
    "200",
    "0,900",
    "0,846",
    "1,000",
    "0,683",
    "API_REBUILD_TOKEN",
]:
    assert fact in text

assert len(text.split()) >= 9000
print("Guide intégral de soutenance : OK")
```

- [ ] **Step 2: Exécuter le contrôle et confirmer l’échec initial**

Run:

```bash
python /tmp/projet7-guide-integral-qa.py
```

Expected: `AssertionError`, car le guide actuel ne contient ni 12 scripts intégraux ni 9 000 mots.

- [ ] **Step 3: Conserver le contrôle pour la vérification finale**

Le fichier reste dans `/tmp` afin de ne pas ajouter un test éditorial au livrable déjà déposé.

### Task 2: Réécrire le guide comme script intégral

**Files:**
- Modify: `outputs/guide-soutenance-openagenda-rag.html`

- [ ] **Step 1: Conserver une navigation adaptée aux 30 minutes**

Le sommaire doit pointer exactement vers :

```html
<a href="#avant-appel">Avant l’appel</a>
<a href="#conducteur">Script des 12 slides</a>
<a href="#demo-live">Démonstration live</a>
<a href="#rapport-depot">Rapport et dépôt</a>
<a href="#questions-jury">Questions du jury</a>
<a href="#plans-secours">Plans de secours</a>
<a href="#debrief">Débrief</a>
```

- [ ] **Step 2: Ajouter la préparation avant l’appel**

La section doit contenir les commandes exactes :

```bash
cd /home/hgbe/openclassrooms/Projet7
conda activate openagenda-rag
docker compose up -d
docker compose ps
curl http://localhost:8000/health
```

Elle doit préciser les fenêtres à ouvrir, les secrets à ne pas montrer et la phrase d’ouverture.

- [ ] **Step 3: Développer les 12 fiches**

Chaque article `class="step"` doit contenir :

```html
<section class="oral-script">
  <h4>Script intégral à lire</h4>
  <p>Texte oral à la première personne...</p>
</section>
```

Puis les neuf blocs obligatoires, les gestes à effectuer, la transition et une section intitulée
`Version courte si je manque de temps`.

- [ ] **Step 4: Ajouter le conducteur complet de la démo**

La section `id="demo-live"` doit couvrir :

- le lancement de `bash scripts/demo_api_5min.sh` ;
- le contrôle de `/health` ;
- le scénario Paris ;
- le scénario Lyon ;
- les éléments JSON à montrer ;
- les phrases à dire pendant l’attente ;
- Docker indisponible, API indisponible et Mistral indisponible ;
- la sortie enregistrée comme solution de secours.

- [ ] **Step 5: Ajouter le parcours du rapport et du dépôt**

La section `id="rapport-depot"` doit fournir le texte oral et l’ordre d’ouverture de :

```text
README.md
src/
scripts/
tests/
data/evaluation/
docker-compose.yml
outputs/rapport-technique-openagenda-rag.pdf
```

- [ ] **Step 6: Développer au moins 20 questions-réponses**

Chaque question doit proposer :

```html
<p><strong>Réponse courte :</strong> réponse directe en 15 à 25 secondes.</p>
<p><strong>Si le jury insiste :</strong> justification, limite et amélioration.</p>
<p><strong>À éviter :</strong> formulation incorrecte ou trop ambitieuse.</p>
```

- [ ] **Step 7: Ajouter les plans de secours et le débrief**

La section `id="plans-secours"` couvre la panne de présentation, Docker, API, réseau Mistral et oubli du texte.
La section `id="debrief"` prépare trois phrases : réussite, limite principale et prochaine étape.

- [ ] **Step 8: Exécuter le contrôle éditorial**

Run:

```bash
python /tmp/projet7-guide-integral-qa.py
```

Expected: `Guide intégral de soutenance : OK`.

- [ ] **Step 9: Commit**

```bash
git add -f outputs/guide-soutenance-openagenda-rag.html
git commit -m "docs: développer le script intégral de soutenance"
```

### Task 3: Vérifier l’affichage et préserver le livrable

**Files:**
- Test: `outputs/guide-soutenance-openagenda-rag.html`
- Verify unchanged: `outputs/openagenda-rag-soutenance.pptx`

- [ ] **Step 1: Démarrer un serveur local**

```bash
python -m http.server 8765 --directory /home/hgbe/openclassrooms/Projet7
```

- [ ] **Step 2: Contrôler la version ordinateur**

Run:

```bash
/home/hgbe/.codex/skills/playwright/scripts/playwright_cli.sh open \
  http://127.0.0.1:8765/outputs/guide-soutenance-openagenda-rag.html
/home/hgbe/.codex/skills/playwright/scripts/playwright_cli.sh snapshot
/home/hgbe/.codex/skills/playwright/scripts/playwright_cli.sh console error
```

Expected: page chargée, sections accessibles et zéro erreur.

- [ ] **Step 3: Contrôler la version mobile**

Run:

```bash
/home/hgbe/.codex/skills/playwright/scripts/playwright_cli.sh resize 390 844
/home/hgbe/.codex/skills/playwright/scripts/playwright_cli.sh snapshot
/home/hgbe/.codex/skills/playwright/scripts/playwright_cli.sh console error
```

Expected: navigation et contenu lisibles sans erreur.

- [ ] **Step 4: Vérifier que le PowerPoint est inchangé et que le dépôt est propre**

Run:

```bash
git diff --check
python /tmp/projet7-refonte-soutenance-qa.py
git status --short
```

Expected: aucun problème de format, 12 slides toujours synchronisées, seuls les changements prévus présents.

- [ ] **Step 5: Vérifier une dernière fois après le commit**

Run:

```bash
python /tmp/projet7-guide-integral-qa.py
git log -1 --oneline
```

Expected: contrôle réussi et commit du guide intégral visible.
