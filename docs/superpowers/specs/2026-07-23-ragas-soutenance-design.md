# Conformite RAGAS et soutenance - conception

## Objectif

Finaliser les livrables de soutenance du POC OpenAgenda RAG avec une evaluation
RAGAS reelle sur trois cas, une demonstration API reproductible en moins de
cinq minutes, un support oral de quinze minutes, un rapport technique conforme
au modele fourni et une presentation PowerPoint de dix a quinze slides.

## Perimetre

Le travail conserve l'architecture existante :

- corpus OpenAgenda/Opendatasoft borne a Paris ;
- index FAISS persistant construit avec `mistral-embed` ;
- generation avec `mistral-small-latest` ;
- orchestration LangChain ;
- API FastAPI et execution Docker.

Les changements portent uniquement sur l'evaluation, la demonstration et les
livrables de soutenance. Ils ne modifient pas la collecte ni le format de
l'index existant.

## Evaluation RAGAS

### Jeu de donnees

Un jeu RAGAS dedie contient au moins trois exemples factuels issus du corpus :

1. Concert Fishers a Paris ;
2. SALON DE LA PHOTO a Paris ;
3. sortie familiale avec visite theatricalisee.

Chaque exemple definit :

- `question` ;
- `reference` factuelle ;
- `retrieved_contexts` produits par le retriever ;
- `response` generee par le moteur RAG ;
- metadonnees d'identification du cas.

Les reponses de reference doivent decrire les faits attendus et non une
instruction abstraite de notation.

### Modeles d'evaluation

RAGAS utilise les integrations LangChain existantes :

- `ChatMistralAI` avec `mistral-small-latest` comme juge ;
- `MistralAIEmbeddings` avec `mistral-embed` pour les metriques semantiques.

Les appels sont sequentiels avec une configuration de nouvelle tentative
adaptee aux limites d'un compte Mistral gratuit. La cle reste chargee depuis
`.env` et n'apparait dans aucun artefact.

### Metriques

Les metriques retenues sont :

- `faithfulness` : fidelite de la reponse aux contextes recuperes ;
- `answer_relevancy` : pertinence de la reponse par rapport a la question ;
- `context_precision` : proportion et classement des contextes utiles ;
- `answer_correctness` : proximite factuelle avec la reponse de reference.

Les sorties comprennent :

- `outputs/evaluation/ragas_results.json`, detail par exemple ;
- `outputs/evaluation/ragas_examples.csv`, tableau lisible ;
- un resume agregant les moyennes et le statut de chaque cas.

Chaque ligne documente la question, les contextes, la reponse, les scores et
une interpretation qualitative. Aucun score n'est invente : le deck et le
rapport ne reprennent que les valeurs effectivement produites.

## Demonstration API

Un script `scripts/demo_api_5min.sh` :

- attend la disponibilite de `GET /health` ;
- execute un cas nominal sur un evenement parisien connu ;
- execute un cas limite hors perimetre Paris ;
- affiche les reponses et les sources ;
- mesure la duree totale ;
- echoue si la duree depasse 300 secondes ;
- ecrit `outputs/demo/demo_api_timing.json`.

Le script ne lance pas `/rebuild`, car une reconstruction complete serait trop
longue et instable pendant une soutenance. La route est montree dans Swagger et
expliquee oralement.

## Soutenance blanche

Le support oral comporte :

- `docs/soutenance/script_soutenance_15min.md`, decoupe par slide avec une
  duree cible totale de quinze minutes ;
- `docs/soutenance/questions_reponses.md`, avec au moins douze questions et
  reponses couvrant metier, donnees, RAG, Mistral, FAISS, API, Docker,
  evaluation, securite, cout et mise en production.

Une repetition chronometree est simulee a partir des temps cibles du script,
puis la demonstration API est reellement chronometree. Le document distingue
clairement temps planifie et temps mesure.

## Presentation PowerPoint

Le deck existant est conserve comme reference visuelle et reste limite a quinze
slides :

1. contexte Puls-Events ;
2. besoin metier ;
3. fonctionnement simple d'un RAG ;
4. corpus OpenAgenda et perimetre Paris ;
5. architecture complete ;
6. pretraitement et qualite des donnees ;
7. chunking, embeddings et FAISS ;
8. chatbot et prompting ;
9. API FastAPI et Docker ;
10. demonstration en moins de cinq minutes ;
11. methode RAGAS ;
12. exemples RAGAS 1 et 2 ;
13. exemple RAGAS 3 et resultats agreges ;
14. limites ;
15. ameliorations et conclusion.

Les slides RAGAS affichent les questions, un extrait compact du contexte, la
reponse, les scores et une interpretation. Le deck ne presente plus les
metriques locales precedentes comme des resultats RAGAS.

## Rapport technique

Le modele
`/home/hgbe/Téléchargements/Template+de+rapport+technique (1).docx` est utilise
comme structure de reference. Le rapport final est enregistre sous
`outputs/rapport-technique-openagenda-rag.docx`.

Il complete les dix rubriques du modele :

1. objectifs du projet ;
2. architecture du systeme ;
3. preparation et vectorisation des donnees ;
4. choix du modele NLP ;
5. construction de la base vectorielle ;
6. API et endpoints exposes ;
7. evaluation du systeme ;
8. recommandations et perspectives ;
9. organisation du depot ;
10. annexes.

La section evaluation contient les trois exemples RAGAS et les resultats reels.
Les annexes incluent un exemple de requete API, le prompt systeme et les
commandes de reproduction.

## Gestion des erreurs

- Une absence de cle Mistral produit un message explicite.
- Une dependance RAGAS absente produit une instruction d'installation.
- Une limite de debit Mistral declenche les nouvelles tentatives configurees,
  puis un echec explicite sans fabriquer de score.
- Un contexte ou une reponse vide invalide l'exemple avant l'appel RAGAS.
- Le script de demonstration retourne un code non nul si l'API est
  indisponible, si un appel echoue ou si la limite de cinq minutes est depassee.

## Tests et verification

L'implementation suit une approche TDD :

- tests de transformation des reponses RAG en echantillons RAGAS ;
- tests de serialisation des scores et interpretations ;
- tests du resume agrege ;
- test du script de chronometrage avec reponses HTTP simulees ;
- suite Pytest complete sans regression.

Les validations finales comprennent :

- evaluation RAGAS reelle sur au moins trois cas ;
- execution chronometree du script de demonstration ;
- rendu et inspection visuelle de chaque page du DOCX ;
- rendu et inspection visuelle de chaque slide du PPTX ;
- verification du nombre de slides et de l'absence de debordements ;
- coherence des chiffres entre JSON, CSV, README, rapport et presentation.

## Criteres d'acceptation

- Le deck contient entre dix et quinze slides et couvre toutes les rubriques
  demandees.
- Trois exemples RAGAS reels sont documentes avec question, contexte, reponse,
  scores et interpretation.
- La demonstration API nominale et limitee s'execute en moins de cinq minutes.
- Le script oral couvre quinze minutes et au moins douze questions sont
  preparees.
- Le rapport final suit les dix sections du modele fourni.
- Aucun secret n'est expose dans les fichiers generes.
