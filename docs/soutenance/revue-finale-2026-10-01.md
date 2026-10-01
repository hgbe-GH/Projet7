# Revue de livraison — 1er octobre 2026

La revue porte sur la mission Puls-Events du document fourni, les notes de
mentorat et les livrables du dépôt. Les exercices de cours ne sont pas des
exigences supplémentaires de la mission.

| Exigence | Preuve vérifiée | Limite à présenter |
|---|---|---|
| Système LangChain, Mistral, FAISS | Modules métier ; seed de 7 586 événements ; 14 903 vecteurs de 1 024 dimensions | Corpus Paris figé en juillet ; actualisation nécessaire |
| Scripts de collecte et reconstruction | `fetch_events.py`, `build_index.py`, `/rebuild` et tests | Reconstruction non relancée pendant la préparation pour préserver la démo ; pas de bascule atomique |
| API REST et Swagger | `/health`, `/docs`, `/ask` réels ; test `api_test.py` | Health ne teste pas Mistral ; `/rebuild` protégé seulement si un jeton est défini |
| Démo live | Deux scénarios réels avec Ministral 8B ; réponses et horodatage sauvegardés | Modèle changé après HTTP 429 sur Small ; conseils hors contexte encore possibles |
| Rapport technique | README et PDF/Word actualisés avec état du 1er octobre | Évaluations de juillet distinguées de la démo actuelle |
| Jeu annoté et métriques | Quatre cas locaux, trois cas RAGAS, scripts et sorties versionnés | Échantillon trop petit ; règles locales permissives ; modèle alternatif à réévaluer |
| Tests automatisés | 76 tests locaux passants | Fournisseurs simulés ; disponibilité externe vérifiée séparément |
| PowerPoint 10 à 15 slides | 12 slides et notes ; export rendu et contrôle de débordement | Présentation à répéter avec les gestes |
| Explications et contexte métier | Guide, glossaire, conducteur 900 secondes, questions du jury | 15 min de présentation, 10 min de discussion, 5 min de débrief |
| Livraison GitHub et archive | Sources, supports, seed et preuves sélectionnées ; ZIP avec lien et noms de juillet 2026 | Dépôt du ZIP sur OpenClassrooms à effectuer par l’étudiant |

Corrections du jour : erreurs fournisseur contrôlées, arrêt des 60 reprises,
date et statut temporel dans le contexte, traçabilité des appels, code de
sortie correct du test API, publication des supports auparavant ignorés,
rapport et archive actualisés. Aucun score RAGAS nouveau n’est inventé.

Les limites ouvertes sont des travaux de produit : données actualisées et
horizon futur, filtres ville/date, refus calibré, jeu annoté plus large,
authentification, supervision, CI/CD et tests de charge. Cette livraison
prépare une soutenance de POC ; elle ne prétend pas livrer un service de
production ni une qualité parfaite.
