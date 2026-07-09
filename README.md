# OpenAgenda RAG Setup

Ce depot couvre actuellement les etapes 1 a 3 du projet OpenClassrooms :

- environnement Python reproductible ;
- collecte et normalisation des evenements OpenAgenda via le dataset public Opendatasoft fourni dans la mission ;
- vectorisation Mistral et index FAISS local.

Le chatbot RAG, l'API REST, l'evaluation, Docker et la demo produit restent hors perimetre a ce stade.

## Structure

```text
.
├── environment.yml
├── requirements.txt
├── README.md
├── scripts/
│   ├── check_env.py
│   ├── build_index.py
│   ├── fetch_events.py
│   └── find_agendas.py
├── src/
│   └── openagenda_rag/
│       ├── ingestion.py
│       ├── indexing.py
│       └── settings.py
└── tests/
    ├── conftest.py
    ├── test_indexing.py
    └── test_ingestion.py
```

## Etape 1 - Environnement reproductible

### Prerequis

- Conda installe localement.
- Python 3.12 sera provisionne par `environment.yml`.
- Une connexion internet pour installer les dependances.
- Une cle Mistral uniquement si vous voulez executer le smoke test d'embedding reel.

### Installation

```bash
conda env create -f environment.yml
conda activate openagenda-rag
PYTHONNOUSERSITE=1 python -m pip install --no-user -r requirements.txt
```

`environment.yml` fournit la base Conda.
`requirements.txt` reste la source de verite des bibliotheques Python du projet.

### Variables d'environnement

Copiez `.env.example` vers `.env`.

Exemple minimal pour les etapes 1 et 2 :

```bash
OPENDATASOFT_BASE_URL=https://public.opendatasoft.com/api/explore/v2.1
OPENDATASOFT_DATASET=evenements-publics-openagenda
OPENAGENDA_CITY=Paris
MISTRAL_API_KEY=...
```

Variables disponibles :

- `OPENDATASOFT_BASE_URL` : base de l'API publique exposee par la source de la mission.
- `OPENDATASOFT_DATASET` : dataset a interroger. Par defaut `evenements-publics-openagenda`.
- `OPENAGENDA_AGENDA_UID` : filtre optionnel sur `originagenda_uid`.
- `OPENAGENDA_SEARCH` : mot-cle pour le helper `scripts/find_agendas.py`.
- `OPENAGENDA_CITY` : filtre de ville.
- `OPENAGENDA_START_DATE` : borne basse inclusive. Par defaut : aujourd'hui - 365 jours.
- `OPENAGENDA_END_DATE` : borne haute inclusive.
- `OPENAGENDA_CATEGORY_FIELD` : champ utilise pour le filtrage local des categories, par exemple `keywords_fr`.
- `OPENAGENDA_CATEGORY_IDS` : liste separee par des virgules des categories a conserver.
- `MISTRAL_API_KEY` : cle Mistral pour le smoke test et l'etape 3.
- `MISTRALAI_API_KEY` : alias accepte par certaines integrations.
- `INDEX_INPUT_PATH` : parquet normalise a indexer.
- `INDEX_OUTPUT_DIR` : dossier de sortie de l'index FAISS.
- `INDEX_EMBEDDING_MODEL` : modele d'embedding Mistral, par defaut `mistral-embed`.
- `INDEX_BATCH_SIZE` : taille de lot employee pendant la construction de l'index.

### Smoke test

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

Si `MISTRAL_API_KEY` est defini, le script execute aussi un appel reel d'embedding.

### Note sur les imports du brief

Le brief cite des imports historiques :

```python
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from mistral import MistralClient
```

Ils sont maintenant remplaces par les chemins maintenus :

```python
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from mistralai.client import Mistral
```

Ce choix evite de figer le projet sur des APIs devenues legacy.

## Etape 2 - Collecte et structuration OpenAgenda

La mission renvoie vers cette source publique :

- `https://public.opendatasoft.com/explore/assets/evenements-publics-openagenda/view/`

L'etape 2 est donc implementee a partir du dataset Opendatasoft `evenements-publics-openagenda`, qui reproduit les evenements OpenAgenda dans un format public interrogeable sans cle API.

### Ce que fait la collecte

- filtre les evenements par periode via l'API ;
- peut filtrer par ville et agenda d'origine ;
- normalise les champs utiles pour l'indexation future ;
- prepare `text_for_embedding` des cette etape ;
- tolere les donnees manquantes sans casser le pipeline ;
- exporte le brut, le dataset structure et un manifeste de collecte.

### Aide au choix d'un agenda

Si vous voulez restreindre la collecte a un agenda d'origine :

```bash
python scripts/find_agendas.py --search "paris"
```

Ce helper balaie des evenements recents du dataset public et deduit les couples `originagenda_uid` / `originagenda_title`.

### Commande de collecte

Exemple simple par ville :

```bash
python scripts/fetch_events.py \
  --city Paris \
  --start-date 2025-07-09
```

Exemple avec borne haute :

```bash
python scripts/fetch_events.py \
  --city Paris \
  --start-date 2025-07-09 \
  --end-date 2026-07-09
```

Exemple avec agenda d'origine et filtrage local par categories :

```bash
python scripts/fetch_events.py \
  --agenda-uid 979472 \
  --city Paris \
  --start-date 2025-07-09 \
  --category-field keywords_fr \
  --category-id nature \
  --category-id culture
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

### Tests couverts

- pagination multi-pages ;
- construction de la clause `where` ;
- normalisation d'evenements incomplets ;
- nettoyage HTML ;
- filtrage par ville ;
- filtrage par categorie ;
- deduplication par `event_uid`.

Execution :

```bash
pytest -q
```

## Etape 3 - Index FAISS

L'etape 3 suppose que `data/processed/events.parquet` existe deja.

Commande minimale :

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
  --rebuild
```

Sorties :

- `data/index/faiss/`
- `data/index/index_manifest.json`
- `data/index/indexed_documents.parquet`

L'indexation conserve les metadonnees suivantes :

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
