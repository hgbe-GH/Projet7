# Script oral de soutenance - 15 minutes

Ce conducteur est synchronisé avec les 15 diapositives du fichier
`outputs/openagenda-rag-soutenance.pptx`. Les durées indiquées totalisent
exactement **15 min 00 s**.

## 00:00-00:45 - Slide 1 : contexte et objectif (45 s)

**À dire**

Bonjour. Je vais vous présenter le POC réalisé pour Puls-Events : un assistant
capable de recommander des événements culturels à partir de données OpenAgenda.
L'objectif était de vérifier la faisabilité d'un système RAG complet, depuis la
collecte des données jusqu'à une API conteneurisée. Le corpus livré est centré
sur Paris et contient 7 586 événements collectés sur une fenêtre récente d'un
an.

**À montrer**

Pointer le périmètre Paris, les volumes du corpus et la chaîne
Mistral-FAISS-FastAPI-Docker.

## 00:45-01:35 - Slide 2 : besoin métier (50 s)

**À dire**

Le besoin métier est simple : permettre à une personne d'exprimer une envie en
langage naturel, puis obtenir des propositions utiles et vérifiables. Une
recherche par mots-clés seule gère mal les formulations variées. Un LLM seul
peut inventer des événements. Le POC combine donc recherche sémantique et
génération, tout en renvoyant les sources, les dates, les lieux et les liens.

## 01:35-02:25 - Slide 3 : expliquer le RAG (50 s)

**À dire**

Un RAG fonctionne en trois temps. D'abord, la question est transformée en
vecteur et comparée aux événements dans FAISS. Ensuite, les meilleurs passages
sont assemblés comme contexte. Enfin, Mistral rédige une réponse uniquement à
partir de ce contexte. Le modèle ne mémorise donc pas le catalogue : il consulte
les données pertinentes au moment de répondre.

## 02:25-03:20 - Slide 4 : données et périmètre (55 s)

**À dire**

Les données viennent du jeu public OpenAgenda exposé par Opendatasoft. La
collecte est reproductible avec `fetch_events.py`. Le seed livré filtre la ville
de Paris et une fenêtre du 10 juillet 2025 au 10 juillet 2026. Chaque événement
est normalisé avec un titre, une description, un lieu, des dates, une URL et les
catégories disponibles. Les valeurs absentes sont gérées sans casser le
pipeline.

## 03:20-04:20 - Slide 5 : architecture globale (60 s)

**À dire**

L'architecture sépare six responsabilités : collecte, nettoyage, découpage,
vectorisation, génération et exposition HTTP. Cette séparation rend chaque
étape testable et remplaçable. Les scripts publics pilotent les modules placés
dans `src/openagenda_rag`. Les données structurées, l'index et les manifestes
sont des artefacts inspectables, ce qui simplifie la reproduction et le
diagnostic.

## 04:20-05:15 - Slide 6 : préparation des données (55 s)

**À dire**

Le nettoyage transforme les réponses hétérogènes de l'API en un schéma stable.
Le champ `text_for_embedding` concatène les informations utiles. Les filtres de
ville et de période sont vérifiés, les doublons sont supprimés par identifiant
d'événement, et le parquet final est directement exploitable par l'indexeur.
Des tests couvrent les données incomplètes, la pagination et la stabilité du
schéma.

## 05:15-06:15 - Slide 7 : embeddings et FAISS (60 s)

**À dire**

Les textes sont découpés en chunks de 1 000 caractères avec un chevauchement de
200 caractères. Le modèle `mistral-embed` produit les vecteurs. FAISS stocke
14 903 chunks correspondant aux 7 586 événements, avec leurs métadonnées. Ce
choix donne une recherche locale rapide et portable. L'index est sauvegardé,
rechargeable et accompagné d'un manifeste qui permet de contrôler le nombre de
documents indexés.

## 06:15-07:15 - Slide 8 : chatbot et garde-fous (60 s)

**À dire**

Pour une question, le retriever renvoie les chunks les plus proches. Le prompt
demande une réponse française, concise, avec justification. Le modèle de chat
est `mistral-small-latest`. Si le contexte ne contient pas l'information, le
système doit dire qu'il ne sait pas. L'historique de conversation n'est pas
nécessaire dans ce POC, ce qui garde le comportement simple et reproductible.

## 07:15-08:05 - Slide 9 : API et Docker (50 s)

**À dire**

FastAPI expose `GET /health`, `POST /ask` et `POST /rebuild`, avec Swagger sur
`/docs`. Le service garde le retriever et le modèle en mémoire pour ne pas les
recharger à chaque question. Docker embarque un seed, puis le copie dans un
volume persistant. La clé Mistral reste injectée par variable d'environnement
et `/rebuild` peut être protégé par un jeton d'administration.

## 08:05-09:20 - Slide 10 : démonstration API (75 s)

**À faire**

Afficher un terminal puis exécuter :

```bash
bash scripts/demo_api_5min.sh
```

**À dire pendant l'exécution**

Le script contrôle d'abord `/health`. Le cas nominal demande des informations
sur Concert Fishers à Paris : l'API renvoie la date, le lieu, le lien et les
sources. Le cas limite demande une exposition photo à Lyon alors que le corpus
est limité à Paris : le système répond qu'il ne sait pas. La répétition mesurée,
démarrage ou contrôle de disponibilité inclus, a duré 2,406 secondes, très en
dessous de la limite de cinq minutes.

## 09:20-10:15 - Slide 11 : méthode RAGAS (55 s)

**À dire**

J'ai évalué trois questions annotées avec RAGAS et les mêmes modèles Mistral.
Quatre métriques sont calculées : la fidélité vérifie que la réponse est
soutenue par le contexte ; la pertinence mesure l'adéquation à la question ; la
précision du contexte vérifie le classement des passages ; la correction
compare la réponse à la référence humaine. L'exécution est séquentielle pour
respecter le quota du compte gratuit.

## 10:15-11:20 - Slide 12 : exemples RAGAS 1 et 2 (65 s)

**À dire**

Le premier cas porte sur Concert Fishers. Son score global est 0,823 :
le contenu principal est correct et son contexte est classé en première
position. Le deuxième cas porte sur le Salon de la Photo. Il obtient 0,887 :
le contexte est parfaitement classé et la
réponse reprend les informations pratiques, avec quelques détails à surveiller
par rapport à la référence.

## 11:20-12:20 - Slide 13 : exemple 3 et résultats agrégés (60 s)

**À dire**

Le troisième cas est une recherche plus ouverte de visite théâtralisée en
famille. Il obtient 0,862 et retrouve plusieurs propositions. Sur les trois cas,
les moyennes sont : fidélité 0,900, pertinence 0,846, précision du contexte
1,000 et correction 0,683. Le retrieval et la fidélité sont donc solides.
L'amélioration prioritaire concerne l'alignement des réponses avec les
références humaines.

## 12:20-13:15 - Slide 14 : limites (55 s)

**À dire**

Le POC a quatre limites principales. Le corpus est centré sur Paris et sur une
fenêtre figée. La génération dépend d'une connexion à Mistral. Le jeu RAGAS ne
contient que trois exemples, donc il démontre la méthode mais ne constitue pas
un benchmark statistique. Enfin, certaines descriptions OpenAgenda sont
bruitées. Ces limites sont explicites et ne remettent pas en cause la
faisabilité technique.

## 13:15-15:00 - Slide 15 : améliorations et conclusion (105 s)

**À dire**

Les prochaines améliorations sont priorisées. D'abord, élargir le jeu annoté et
tester plusieurs villes. Ensuite, renforcer le prompt pour supprimer les
informations promotionnelles non soutenues et ajouter un seuil de similarité
pour mieux rejeter les questions hors corpus. À moyen terme, on peut automatiser
la collecte, comparer plusieurs modèles d'embeddings et suivre les métriques en
CI.

Pour conclure, le POC couvre toute la chaîne attendue : données réelles,
prétraitement reproductible, index FAISS persistant, chatbot sans API pour les
tests directs, API FastAPI, Docker, démonstration chronométrée et évaluation
RAGAS réelle. Il apporte une preuve de faisabilité exploitable par les équipes
produit, tout en identifiant clairement le travail nécessaire avant une mise en
production. Merci, je suis prêt à répondre à vos questions.

## Contrôle du chronométrage

| Slide | Durée | Cumul |
|---|---:|---:|
| 1 | 0:45 | 0:45 |
| 2 | 0:50 | 1:35 |
| 3 | 0:50 | 2:25 |
| 4 | 0:55 | 3:20 |
| 5 | 1:00 | 4:20 |
| 6 | 0:55 | 5:15 |
| 7 | 1:00 | 6:15 |
| 8 | 1:00 | 7:15 |
| 9 | 0:50 | 8:05 |
| 10 | 1:15 | 9:20 |
| 11 | 0:55 | 10:15 |
| 12 | 1:05 | 11:20 |
| 13 | 1:00 | 12:20 |
| 14 | 0:55 | 13:15 |
| 15 | 1:45 | **15:00** |
