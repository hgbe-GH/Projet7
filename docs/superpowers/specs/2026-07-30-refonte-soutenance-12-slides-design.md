# Refonte de la soutenance en 12 slides - conception

## Objectif

Simplifier le PowerPoint de soutenance et rendre le guide HTML plus pédagogique. Le PowerPoint doit être compris rapidement par le jury. Le HTML doit permettre à Hugo de comprendre ce que réalise chaque composant, pourquoi il existe, comment les données circulent et comment justifier les choix.

## Travail de communication

À la fin des 15 minutes, Jérémy doit comprendre que le POC démontre une chaîne RAG complète, reproductible et mesurée, tout en distinguant clairement la preuve de faisabilité des exigences d'une production.

Le message central est :

> Le POC retrouve des événements réels, génère une réponse sourcée, expose le service par API et rend ses limites mesurables.

## Principes du PowerPoint

- 12 slides au format 16:9.
- Une idée principale par slide.
- Des titres qui expriment une conclusion, pas seulement un thème.
- Peu de texte visible.
- Les chiffres ne sont affichés que lorsqu'ils servent une conclusion.
- Un seul schéma d'architecture complet.
- Un schéma très simple pour expliquer le RAG.
- Les résultats RAGAS sont regroupés en une seule lecture visuelle.
- La démonstration, le rapport et le dépôt sont explicitement intégrés au déroulé.
- Le style visuel existant est conservé dans ses grandes lignes : fond chaud, bleu nuit, accent corail.
- Les répétitions en trois cartes sont supprimées au profit de compositions plus variées.

## Nouvelle narration en 12 slides

### Slide 1 - Le POC démontre toute la chaîne RAG

Présenter la mission Puls-Events, le résultat livré et trois preuves : 7 586 événements, 14 903 chunks, API Docker fonctionnelle.

### Slide 2 - Le RAG évite le choix entre recherche rigide et réponse inventée

Opposer recherche par mots-clés, LLM seul et solution RAG. La conclusion visible doit être : réponse naturelle, fondée sur des événements réels et vérifiable.

### Slide 3 - Une question devient une réponse sourcée en trois étapes

Schéma simple : question → recherche FAISS → contexte → réponse Mistral avec sources.

### Slide 4 - Le corpus est un instantané reproductible de Paris

Montrer la source OpenAgenda/Opendatasoft, la fenêtre 2025-07-10/2026-07-10, les 7 586 événements et les champs normalisés. Indiquer clairement qu'il s'agit d'un snapshot de POC.

### Slide 5 - Chaque responsabilité du pipeline reste isolée et testable

Schéma d'architecture de bout en bout : collecte, préparation, indexation, RAG, API et Docker. Faire apparaître les fichiers ou modules seulement sous forme de repères secondaires.

### Slide 6 - Les descriptions deviennent 14 903 passages recherchables

Expliquer chunks 1000/200, embeddings `mistral-embed`, métadonnées et index FAISS. La conclusion est que le système recherche du sens et conserve les preuves.

### Slide 7 - L'API expose le RAG sans recharger le système à chaque question

Réunir chatbot, `top_k=4`, prompt contraint, cache en mémoire, endpoints FastAPI, Swagger, Docker et sécurité des secrets. N'afficher que les éléments essentiels.

### Slide 8 - La démonstration prouve le cas nominal et la limite

Présenter les deux questions : Concert Fishers à Paris et exposition photo à Lyon. Montrer résultat sourcé, refus d'inventer, durée réelle et parcours rapide du rapport/dépôt.

### Slide 9 - L'évaluation sépare recherche, fidélité et correction

Expliquer quatre cas fonctionnels, trois cas RAGAS et les quatre métriques. Éviter les définitions longues.

### Slide 10 - La recherche est solide, la correction reste prioritaire

Afficher les quatre moyennes : fidélité 0,900, pertinence 0,846, précision du contexte 1,000, correction 0,683. Interpréter immédiatement le résultat et rappeler la taille limitée du jeu.

### Slide 11 - Le POC valide la faisabilité, pas la production

Regrouper les limites : fraîcheur et zone du corpus, dépendance Mistral, absence de seuil de similarité, petit benchmark et qualité variable des descriptions.

### Slide 12 - La prochaine étape est un pilote multi-villes mesuré

Présenter trois priorités : données et benchmark, garde-fous de retrieval, industrialisation. Conclure par une recommandation claire à Jérémy.

## Nouveau guide HTML

Le guide reste un fichier HTML autonome dans `outputs/`. Sa structure est réorganisée autour de la compréhension.

Pour chaque slide, les blocs apparaissent dans cet ordre :

1. **Ce que je cherche à démontrer** - l'idée que le jury doit retenir.
2. **Ce qui entre** - données, question ou artefacts utilisés.
3. **Ce que mon code fait** - transformation réelle, sans jargon inutile.
4. **Ce qui sort** - fichier, index, réponse ou métrique.
5. **Pourquoi ce choix** - justification technique et métier.
6. **Ce que je dis** - discours à la première personne.
7. **Ce que je montre** - action précise dans les slides, le terminal, le rapport ou GitHub.
8. **À ne pas dire** - raccourcis ou affirmations trompeuses.
9. **Question probable** - réponse courte et défendable.

Le guide conserve :

- la checklist immédiate ;
- la démonstration et ses commandes ;
- le parcours du rapport et du dépôt ;
- les explications des notions ;
- le jury blanc complet ;
- les plans de secours ;
- la checklist des cinq dernières minutes.

Le conducteur et les minutages sont recalés sur 12 slides :

- slides 1 à 3 : 3 minutes ;
- slides 4 à 7 : 5 minutes ;
- slide 8 et parcours des livrables : 2 minutes ;
- slides 9 et 10 : 2 minutes 30 ;
- slides 11 et 12 : 2 minutes 30.

## Contraintes de contenu

- Ne pas prétendre que le corpus est automatiquement actuel.
- Distinguer les quatre cas fonctionnels des trois cas RAGAS.
- Ne pas présenter la précision du contexte à 1,000 comme une perfection générale.
- Présenter `top_k=4` et le chunking 1000/200 comme des paramètres de POC à calibrer.
- Dire que FAISS et les données sont locaux, mais que Mistral nécessite Internet.
- Dire que `/rebuild` peut être protégé par `API_REBUILD_TOKEN` et doit l'être en production.
- Ne jamais afficher la valeur d'un secret.

## Vérifications

- Le PowerPoint contient exactement 12 slides.
- Aucun débordement ou chevauchement n'est présent.
- Les textes restent lisibles à distance.
- Chaque slide possède une conclusion claire.
- Le guide contient exactement 12 étapes synchronisées.
- Les faits et métriques correspondent aux fichiers du projet.
- Le HTML fonctionne sur ordinateur et mobile, sans ressource distante.
- Les liens vers le PowerPoint, le rapport et le README sont valides.
- Les 59 tests du projet continuent de passer.
