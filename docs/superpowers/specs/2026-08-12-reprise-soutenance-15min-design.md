# Reprise de soutenance — conception 15 minutes

## Objectif de communication

À la fin de la présentation, Jérémy doit pouvoir décider qu’un pilote mesuré de l’assistant culturel est justifié, car le POC démontre la chaîne complète, explique ses méthodes, mesure ses résultats et expose honnêtement ses limites.

## Réponse au retour du jury

Le retour ne remet pas en cause les livrables. Il demande une présentation d’environ 15 minutes, davantage de contexte et l’explication des méthodes : nettoyage, chunking, tests, RAGAS, limites et industrialisation. Le deck passe donc d’une succession de résultats à un raisonnement complet : problème, données, méthode, preuve, évaluation, décision.

## Format

- 12 slides au format PowerPoint, dans la charte existante.
- Environ 14 minutes 30 de contenu principal, puis 30 à 45 secondes de parcours du rapport et du dépôt.
- Démonstration API de 2 minutes incluse entre les slides 7 et 8.
- Notes orales complètes dans les notes PowerPoint et dans le guide HTML.
- Le rapport et le dépôt sont des preuves à montrer, pas des éléments auxquels renvoyer à la place d’une explication.

## Déroulé

| Slide | Rôle | Durée cible |
|---|---|---:|
| 1 | Décision à instruire pour Puls-Events | 0:55 |
| 2 | Risque métier résolu par le RAG | 1:05 |
| 3 | Nettoyage du corpus OpenAgenda | 1:20 |
| 4 | Exemple réel de chunking et embeddings | 1:20 |
| 5 | Question, prompt contraint et génération | 1:15 |
| 6 | Architecture modulaire | 1:00 |
| 7 | API et déploiement Docker | 0:55 |
| Démo | Cas Paris et cas Lyon hors périmètre | 2:00 |
| 8 | Retour de démo et interprétation | 0:35 |
| 9 | Tests, rapport de test et CI/CD proposée | 1:25 |
| 10 | Méthode RAGAS et interprétation des scores | 1:30 |
| 11 | Limites reconnues | 1:10 |
| 12 | Recommandation et feuille de route | 1:05 |

## Points de méthode visibles

1. Le nettoyage montre source brute, filtres Paris/date, suppression des doublons, retrait du HTML et conservation des métadonnées utiles.
2. Le chunking s’appuie sur un événement réel, `CHIMERE`, qui possède une description de 10 273 caractères. Le slide montre le principe 1 000 caractères / chevauchement 200, l’embedding `mistral-embed` et l’index FAISS.
3. Le prompt montre les règles : seulement le contexte, refus si le contexte ne permet pas de répondre, titres, lieux, dates et URL quand ils existent. Il explique que `mistral-small-latest` formule la réponse alors que l’embedding sert à retrouver.
4. Les tests montrent la stratégie : tests unitaires et API pour ingestion, normalisation, index, RAG, API et évaluation ; cas fonctionnels pour le comportement métier ; RAGAS pour la qualité. Les 59 tests sont présentés comme une preuve de non-régression du code, non comme une preuve absolue de qualité métier.
5. La CI/CD est explicitement proposée, non livrée : push → installation → pytest → image Docker → healthcheck → rapport de test → déploiement seulement si les contrôles passent.
6. RAGAS montre ses entrées, ce qu’il mesure et comment les scores orientent une amélioration. Les trois cas RAGAS sont présentés comme un signal initial, non un benchmark général.

## Rôle de l’évaluateur

Le discours s’adresse à Jérémy. Chaque slide répond à une question utile pour sa décision : quel risque est réduit, quelle preuve est disponible, quelle limite reste ouverte et quelle action est recommandée.

## Hors diaporama

Après la slide 12 : 20 secondes sur le rapport et 20 secondes sur le dépôt. Pendant la discussion : le guide HTML reste hors partage et sert de préparation aux questions. Une demande de code ouvre le module demandé, puis revient à la décision métier.
