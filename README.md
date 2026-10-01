# Rapport technique — assistant RAG de recommandation culturelle

**Soutenance du 1er octobre 2026 à 14 h :** [préparation et checklist](outputs/AVANT-14H.md),
[diaporama HTML](outputs/presentation-soutenance-openagenda-rag.html),
[PowerPoint de 12 slides](outputs/openagenda-rag-soutenance.pptx),
[guide personnel](outputs/guide-soutenance-openagenda-rag.html) et
[rapport PDF actualisé](outputs/rapport-technique-openagenda-rag.pdf).

Pour la démonstration du jour, renseigner `MISTRAL_API_KEY` et
`RAG_CHAT_MODEL=ministral-8b-2512` dans un fichier `.env` personnel, puis lancer :

```bash
docker compose up -d --build
python docs/soutenance/serve_soutenance.py
```

Ouvrir ensuite `http://127.0.0.1:8765`. Les pages et les réponses enregistrées
restent consultables sans réseau ; les appels directs nécessitent Mistral.
Le corpus et les évaluations de juillet sont historiques. Les limites et le
changement de modèle sont décrits dans la dernière section de ce rapport.

POC RAG pour la mission OpenClassrooms "assistant de recommandation d'evenements culturels" pour Puls-Events.

Le depot couvre les etapes 1 a 6 :

- environnement Python reproductible ;
- collecte et structuration d'evenements OpenAgenda via la source publique Opendatasoft de la mission ;
- vectorisation Mistral et index FAISS local ;
- chatbot RAG ;
- API REST FastAPI ;
- livraison Docker reproductible.

Le POC reste local, mais la generation de reponses depend de l'API Mistral en ligne.

## Perimetre final livre

Le corpus versionne dans ce depot correspond au POC :

- zone retenue : `Paris` ;
- fenetre de collecte : du `10 juillet 2025` au `10 juillet 2026` inclus ;
- nombre d'evenements normalises : `7586` ;
- nombre de chunks indexes dans FAISS : `14903`.

Le seed reproductible utilise par Docker est versionne dans `seed-data/`.
Les dossiers `data/` restent des artefacts de travail locaux regenerables.

La borne temporelle est appliquee au moment de la collecte. Certaines lignes peuvent avoir un `last_timing` ulterieur a la borne haute lorsqu'un evenement recurrent a sa premiere occurrence dans la fenetre mais se prolonge ensuite.

## Structure du depot public

```text
.
├── .env.example
├── .dockerignore
├── .gitignore
├── environment.yml
├── requirements.txt
├── README.md
├── Dockerfile
├── docker-compose.yml
├── docs/soutenance/    # sources, conducteur, revue et serveur des supports
├── outputs/            # livrables sélectionnés et preuves versionnés
├── seed-data/
│   ├── index/
│   └── processed/
├── scripts/
│   ├── api_test.py
│   ├── build_index.py
│   ├── chatbot.py
│   ├── check_env.py
│   ├── demo_api_5min.py
│   ├── demo_api_5min.sh
│   ├── demo_scenarios.sh
│   ├── docker_entrypoint.sh
│   ├── evaluate_rag.py
│   ├── evaluate_ragas.py
│   ├── fetch_events.py
│   ├── find_agendas.py
│   └── run_api.py
├── src/
│   └── openagenda_rag/
│       ├── api.py
│       ├── demo.py
│       ├── evaluation.py
│       ├── indexing.py
│       ├── ingestion.py
│       ├── rag.py
│       ├── ragas_evaluation.py
│       ├── service.py
│       └── settings.py
└── tests/
    ├── fixtures/
    │   ├── rag_eval_dataset.csv
    │   └── ragas_eval_dataset.csv
    ├── conftest.py
    ├── test_api.py
    ├── test_evaluation.py
    ├── test_indexing.py
    ├── test_ingestion.py
    ├── test_demo.py
    ├── test_rag.py
    ├── test_ragas_evaluation.py
    └── test_settings.py
```

## Etape 1 - Environnement reproductible

### Prerequis

- Conda installe localement.
- Python `3.12` provisionne par `environment.yml`.
- Connexion internet pour installer les dependances.
- Cle Mistral uniquement pour les appels reels d'embedding et de generation.

### Installation

Toutes les commandes hors Docker supposent que l'environnement Conda du projet est actif.

```bash
conda env create -f environment.yml
conda activate openagenda-rag
PYTHONNOUSERSITE=1 python -m pip install --no-user -r requirements.txt
```

`environment.yml` est la base de reproduction locale.
`requirements.txt` est conserve pour Docker et les installs `pip`.

### Variables d'environnement

Copier `.env.example` vers `.env`.

Exemple minimal :

```bash
OPENDATASOFT_BASE_URL=https://public.opendatasoft.com/api/explore/v2.1
OPENDATASOFT_DATASET=evenements-publics-openagenda
OPENAGENDA_CITY=Paris
MISTRAL_API_KEY=...
```

Variables principales :

- `OPENDATASOFT_BASE_URL` : base URL de l'API publique.
- `OPENDATASOFT_DATASET` : dataset source, par defaut `evenements-publics-openagenda`.
- `OPENAGENDA_AGENDA_UID` : filtre optionnel sur `originagenda_uid`.
- `OPENAGENDA_SEARCH` : mot-cle pour `scripts/find_agendas.py`.
- `OPENAGENDA_CITY` : filtre de ville. Le POC livre utilise `Paris`.
- `OPENAGENDA_START_DATE` : borne basse inclusive. Par defaut `aujourd'hui - 365 jours`.
- `OPENAGENDA_END_DATE` : borne haute inclusive. Par defaut `aujourd'hui`.
- `OPENAGENDA_CATEGORY_FIELD` : champ texte pour un filtrage local de categories.
- `OPENAGENDA_CATEGORY_IDS` : liste de categories separees par des virgules.
- `MISTRAL_API_KEY` : cle Mistral principale.
- `MISTRALAI_API_KEY` : alias compatible avec certaines integrations.
- `INDEX_INPUT_PATH` : parquet normalise a indexer.
- `INDEX_OUTPUT_DIR` : dossier de l'index FAISS.
- `INDEX_EMBEDDING_MODEL` : modele d'embedding, par defaut `mistral-embed`.
- `INDEX_BATCH_SIZE` : taille de lot pour l'indexation.
- `INDEX_CHUNK_SIZE` : taille des chunks texte.
- `INDEX_CHUNK_OVERLAP` : recouvrement des chunks.
- `RAG_CHAT_MODEL` : modele de chat Mistral, par defaut `mistral-small-latest`.
- `RAG_TOP_K` : nombre de chunks recuperes avant generation.
- `RAG_TEMPERATURE` : temperature du modele de chat.
- `RAG_MAX_TOKENS` : longueur maximale de reponse.
- `API_HOST` : hote FastAPI.
- `API_PORT` : port FastAPI.
- `API_REBUILD_TOKEN` : jeton optionnel pour proteger `/rebuild`.

### Verification de l'environnement

```bash
PYTHONNOUSERSITE=1 python scripts/check_env.py
PYTHONNOUSERSITE=1 python -m pip check
```

`check_env.py` valide :

- `import faiss`
- `from langchain_community.vectorstores import FAISS`
- `from langchain_huggingface import HuggingFaceEmbeddings`
- `from langchain_mistralai import MistralAIEmbeddings`
- `from mistralai.client import Mistral`

Si `MISTRAL_API_KEY` est defini, le script lance aussi un appel reel d'embedding.

### Note sur les imports du brief

Le brief cite des imports legacy :

```python
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from mistral import MistralClient
```

Le projet utilise les chemins maintenus :

```python
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_mistralai import MistralAIEmbeddings
from mistralai.client import Mistral
```

## Etape 2 - Collecte et structuration OpenAgenda

La mission renvoie vers la source publique :

- `https://public.opendatasoft.com/explore/assets/evenements-publics-openagenda/view/`

Le projet interroge donc le dataset Opendatasoft `evenements-publics-openagenda`, expose sans cle.

### Ce que fait la collecte

- filtre les evenements par periode cote API ;
- peut filtrer par ville et agenda d'origine ;
- normalise les champs utiles a l'indexation ;
- prepare `text_for_embedding` des cette etape ;
- tolere les donnees manquantes ;
- exporte le brut, le parquet et un manifeste de collecte.

### Helper agenda

Pour chercher un agenda d'origine avant de figer un `originagenda_uid` :

```bash
python scripts/find_agendas.py --search "paris"
```

### Commande de collecte

Exemple principal du POC livre :

```bash
python scripts/fetch_events.py --city Paris
```

Exemple explicite avec bornes :

```bash
python scripts/fetch_events.py \
  --city Paris \
  --start-date 2025-07-10 \
  --end-date 2026-07-10
```

Exemple avec agenda et categories :

```bash
python scripts/fetch_events.py \
  --agenda-uid 979472 \
  --city Paris \
  --start-date 2025-07-10 \
  --end-date 2026-07-10 \
  --category-field keywords_fr \
  --category-id culture \
  --category-id musique
```

Priorite de configuration : `CLI > .env > valeurs par defaut`.

### Sorties generees

- `data/raw/openagenda_events.json`
- `data/processed/events.parquet`
- `data/processed/fetch_manifest.json`

### Schema normalise

- `event_uid`
- `agenda_uid`
- `title`
- `summary`
- `long_description`
- `text_for_embedding`
- `city`
- `location_name`
- `latitude`
- `longitude`
- `first_timing`
- `last_timing`
- `timezone`
- `canonical_url`
- `categories`
- `source_updated_at`
- `raw_event`

### Corpus versionne actuellement

Le manifeste [seed-data/processed/fetch_manifest.json](seed-data/processed/fetch_manifest.json) documente le corpus livre :

- `generated_at` : `2026-07-10T13:10:27.381850+00:00`
- `city` : `Paris`
- `start_date` : `2025-07-10`
- `end_date` : `2026-07-10`
- `normalized_event_count` : `7586`

## Etape 3 - Vectorisation et index FAISS

L'etape 3 consomme `data/processed/events.parquet`.

Chaque evenement est converti en texte, decoupe en chunks, vectorise avec Mistral puis indexe localement dans FAISS.

### Build de l'index

```bash
python scripts/build_index.py
```

Exemple complet :

```bash
python scripts/build_index.py \
  --input-path data/processed/events.parquet \
  --output-dir data/index/faiss \
  --embedding-model mistral-embed \
  --batch-size 50 \
  --chunk-size 1000 \
  --chunk-overlap 200 \
  --rebuild
```

### Sorties

- `data/index/faiss/`
- `data/index/index_manifest.json`
- `data/index/indexed_documents.parquet`

Le manifeste [seed-data/index/index_manifest.json](seed-data/index/index_manifest.json) du corpus livre indique :

- `generated_at` : `2026-07-10T13:16:17.439399+00:00`
- `indexed_event_count` : `7586`
- `indexed_document_count` : `14903`
- `embedding_model` : `mistral-embed`

### Metadonnees conservees dans FAISS

- `chunk_id`
- `chunk_index`
- `chunk_start`
- `event_uid`
- `agenda_uid`
- `title`
- `city`
- `location_name`
- `first_timing`
- `last_timing`
- `timezone`
- `canonical_url`
- `categories`
- `source_updated_at`

## Etape 4 - Chatbot RAG

Le moteur RAG recharge l'index FAISS, recupere les chunks les plus proches puis interroge Mistral pour produire une reponse en francais avec sources.

### Utilisation

Question simple :

```bash
python scripts/chatbot.py --question "Parle-moi de Concert Fishers a Paris"
```

Sortie JSON :

```bash
python scripts/chatbot.py --question "Parle-moi de SALON DE LA PHOTO a Paris" --json
```

Mode interactif :

```bash
python scripts/chatbot.py
```

Options principales :

- `--index-dir`
- `--embedding-model`
- `--chat-model`
- `--top-k`
- `--temperature`
- `--max-tokens`

## Etape 5 - API REST FastAPI

Routes exposees :

- `GET /health`
- `POST /ask`
- `POST /rebuild`
- `/docs`

### Demarrage local

```bash
python scripts/run_api.py
```

Alternative :

```bash
uvicorn openagenda_rag.api:app --app-dir src --host 127.0.0.1 --port 8000
```

### Exemple `/ask`

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Parle-moi de Concert Fishers a Paris"}'
```

### Exemple `/rebuild`

```bash
curl -X POST http://127.0.0.1:8000/rebuild \
  -H "Content-Type: application/json" \
  -d '{}'
```

Avec protection optionnelle :

```bash
curl -X POST http://127.0.0.1:8000/rebuild \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: votre_token" \
  -d '{"chunk_size": 1000, "chunk_overlap": 200}'
```

### Test fonctionnel HTTP

```bash
python scripts/api_test.py
```

## Etape 6 - Docker et demo

L'image Docker embarque le seed versionne de `seed-data/processed` et
`seed-data/index`, puis le copie dans `/app/runtime-data` au premier demarrage
afin de garder `/rebuild` utile avec un volume persistant.

### Variables Docker

- `MISTRAL_API_KEY`
- `API_HOST`
- `API_PORT`
- `API_REBUILD_TOKEN`
- `INDEX_OUTPUT_DIR=/app/runtime-data/index/faiss`
- `INDEX_INPUT_PATH=/app/runtime-data/processed/events.parquet`

### Build

```bash
docker build -t openagenda-rag .
```

### Run compose

```bash
docker compose up --build
```

### Verification

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/openapi.json`

### Demo script

```bash
bash scripts/demo_api_5min.sh
```

Ce script verifie `/health`, execute un cas nominal et un cas limite, mesure la
duree totale et enregistre un compte rendu local ignore par Git.

- cas nominal : `Parle-moi de Concert Fishers a Paris`
- cas limite : `Quelles expositions photo a Lyon ?`

La repetition livree a dure `2,406 s`, sous la limite de cinq minutes. Le cas
limite repond explicitement qu'aucune exposition photo a Lyon n'est presente,
sans inventer d'evenement.

Le script historique a trois questions reste disponible :

```bash
bash scripts/demo_scenarios.sh
```

## Evaluation automatisee

Le depot contient un petit jeu de test annote versionne :

- [tests/fixtures/rag_eval_dataset.csv](tests/fixtures/rag_eval_dataset.csv)

Colonnes :

- `question`
- `expected_answer`
- `expected_event_titles`
- `notes`

Le jeu couvre :

- un cas positif precis ;
- des cas agreges avec plusieurs evenements possibles ;
- un cas negatif hors corpus.

### Lancer l'evaluation

Mode direct :

```bash
python scripts/evaluate_rag.py
```

Mode API :

```bash
python scripts/evaluate_rag.py --mode api --base-url http://127.0.0.1:8000
```

Options utiles :

- `--dataset-path`
- `--mode direct|api`
- `--base-url`
- `--output-path`
- `--summary-path`
- `--timeout`
- `--ragas`

### Metriques calculees

- `exact_match_soft` : comparaison sur texte normalise.
- `lexical_similarity` : similarite lexicale simple.
- `matched_expected_titles` : titres attendus retrouves dans la reponse ou dans les sources.
- `classification` : `correct`, `partial`, `incorrect`.

Regle de lecture pratique :

- `correct` : tous les titres attendus du cas sont bien recuperes, ou bien le systeme refuse correctement une question hors corpus.
- `partial` : couverture utile mais incomplete.
- `incorrect` : mauvais evenement, absence de source utile, ou refus non justifie.

Les resultats detailles et leur synthese sont generes localement et ignores par
Git afin de conserver un depot public centre sur le code, les donnees de
reference et la reproductibilite.

## Evaluation RAGAS reelle

Le fichier [tests/fixtures/ragas_eval_dataset.csv](tests/fixtures/ragas_eval_dataset.csv)
contient trois references factuelles. L'evaluation utilise les contextes
exactement transmis au modele de generation, puis calcule quatre metriques
RAGAS avec Mistral :

```bash
python scripts/evaluate_ragas.py
```

L'execution est sequentielle avec reprises automatiques pour respecter les
limites d'un compte Mistral gratuit.

### Resultats livres

| Metrique | Moyenne | Interpretation |
|---|---:|---|
| Fidelite au contexte | `0,900` | fort |
| Pertinence de la reponse | `0,846` | fort |
| Precision du contexte | `1,000` | fort |
| Correction de la reponse | `0,683` | acceptable |

Les trois exemples documentes sont :

| Question | Score global | Lecture |
|---|---:|---|
| Concert Fishers a Paris | `0,823` | contexte principal correctement classe |
| SALON DE LA PHOTO a Paris | `0,887` | fidelite et precision du contexte fortes |
| Sortie en famille avec visite theatralisee | `0,862` | plusieurs sources utiles retrouvees |

Chaque ligne generee conserve la question, les contextes recuperes, la reponse,
la reference humaine, les scores et leur interpretation.

Ces trois cas demontrent la methode d'evaluation ; ils ne constituent pas un
benchmark statistique.

## Tests

Suite complete :

```bash
python -m pytest -q
```

Les tests couvrent notamment :

- ingestion et pagination ;
- normalisation et filtres ;
- construction et rechargement d'index FAISS ;
- structure de reponse du moteur RAG et de l'API ;
- lecture du jeu annote et scoring d'evaluation ;
- construction et serialisation des exemples RAGAS ;
- reprises des erreurs temporaires de metriques ;
- chronometrage de la demonstration API ;
- valeurs par defaut des dates de collecte.

## Matrice de conformite aux livrables

| Exigence de la mission | Element public fourni |
|---|---|
| Systeme RAG LangChain, Mistral et FAISS | `src/openagenda_rag/rag.py`, `src/openagenda_rag/indexing.py`, `src/openagenda_rag/service.py` |
| Reconstruction de l'index depuis les donnees | `scripts/fetch_events.py`, `scripts/build_index.py` |
| API REST exploitable | `src/openagenda_rag/api.py`, `scripts/run_api.py`, documentation Swagger sur `/docs` |
| Rapport technique | ce `README.md` : architecture, technologies, modeles, resultats, limites et ameliorations |
| Tests unitaires | `tests/` |
| Jeu de test annote | `tests/fixtures/rag_eval_dataset.csv`, `tests/fixtures/ragas_eval_dataset.csv` |
| Metriques automatisees | `scripts/evaluate_rag.py`, `scripts/evaluate_ragas.py` |
| Corpus recent et reproductible | `seed-data/processed/`, fenetre de moins d'un an documentee ci-dessus |
| Index FAISS pret a tester | `seed-data/index/` |
| Conteneurisation et demo API | `Dockerfile`, `docker-compose.yml`, `scripts/demo_api_5min.sh` |

## Limites du POC

- Le POC est volontairement borne a `Paris` pour la soutenance.
- La generation depend de Mistral en ligne ; la demo n'est donc pas completement offline.
- L'evaluation fournie est petite et orientee reproductibilite, pas benchmark grande echelle.
- La qualite de reponse depend fortement du corpus livre et de la formulation des questions.
- Les scores RAGAS peuvent varier legerement entre deux appels au modele juge.
- Le POC ne comprend pas encore de seuil de similarite bloquant avant la generation.

## Pistes d'amelioration

- elargir le corpus a plusieurs villes et automatiser son rafraichissement ;
- ajouter un seuil de pertinence et une strategie de refus plus robuste ;
- enrichir les filtres metier sur la date, la distance, le public et l'accessibilite ;
- augmenter et diversifier le jeu annote pour produire des intervalles de confiance ;
- suivre latence, cout, qualite et derive des donnees dans un environnement de production ;
- ajouter authentification, limitation de debit et observabilite avant industrialisation.

### Vérification de soutenance du 1er octobre 2026

Le modèle historique du POC et des évaluations de juillet reste
`mistral-small-latest`. Lors de la préparation, cette génération a renvoyé
HTTP 429, tandis que `mistral-embed` répondait HTTP 200 avec la même clé.
Pour la démonstration, `.env` configure désormais
`RAG_CHAT_MODEL=ministral-8b-2512`. Les embeddings et l’index FAISS restent
compatibles : aucun réindexage n’a été nécessaire. Ce choix permet de
rétablir la démo ; les scores historiques ne mesurent pas ce modèle alternatif.

L’API traite désormais les erreurs HTTP fournisseur (limite 429 et accès :
503 ; autres réponses d’erreur : 502) et les erreurs réseau (503), sans
exposer les détails des exceptions fournisseur ou inattendues. Le script
de démonstration s’arrête au premier échec plutôt que de répéter 60 fois les
appels. Le prompt reçoit la date du jour et un statut temporel calculé à
partir des métadonnées ; ce statut n’est pas un filtre de recherche et ne
remplace pas l’actualisation du corpus.

Les 76 tests locaux passent. Les réponses des deux scénarios réels, la
configuration `/health`, l’horodatage et la durée globale sont conservés dans
`outputs/demo/demo_api_2026-10-01.json`. La qualité doit encore être contrôlée :
le modèle peut ajouter un conseil général hors contexte malgré les consignes.
Les supports et le guide personnel sont servis par
`python docs/soutenance/serve_soutenance.py` sur `http://127.0.0.1:8765`.
