# Refonte visuelle de la soutenance RAG

## Objectif de communication

À la fin de la présentation, Jérémy doit pouvoir décider de lancer un pilote mesuré, car les choix techniques, les preuves de qualité et les limites du POC sont compris en un coup d’œil.

## Public et contrainte

- Public : évaluateur jouant le responsable technique de Puls-Events.
- Durée : environ 15 minutes, démo incluse.
- Support : 12 slides, complétées par les notes du présentateur et l’antisèche HTML.
- Contrat : conserver le thème visuel existant et les faits vérifiés du dépôt ; ne pas transformer la CI/CD proposée en fonctionnalité livrée.

## Direction visuelle retenue

Une présentation visuelle et sobre : 3 à 4 photos culturelles seulement pour installer le contexte métier ; pour le contenu technique, de grands schémas éditoriaux, des chiffres lisibles et des exemples concrets. Les détails ne sont pas entassés sur les slides : ils restent dans les notes du présentateur.

Les éléments à éviter sont les grilles répétées de cartes, les paragraphes, les captures artificielles d’API et les photos décoratives sans rôle de compréhension.

## Structure de la refonte

1. Décision à prendre et preuves du POC.
2. Risque d’un chatbot non sourcé, puis rôle du RAG.
3. Passage visible des données brutes au corpus propre.
4. Zoom sur un véritable événement et son chunking.
5. Flux question → retrieval → prompt → réponse sourcée.
6. Chaîne technique hors ligne / en ligne.
7. Contrat API et conteneurisation.
8. Démonstration avec cas Paris et cas Lyon hors périmètre.
9. Pyramide de contrôle : tests livrés et CI/CD proposée.
10. Évaluation RAGAS comme diagnostic, avec la correction en priorité.
11. Limites classées par risque et action corrective.
12. Feuille de route de pilote comme recommandation finale.

## Règles de composition

- Une idée centrale par slide, formulée dans le titre.
- Une seule visualisation principale par slide : flux, comparaison, zoom, frise ou matrice de décision.
- Visible : un chiffre ou une preuve forte ; oral : l’explication complète.
- Couleurs existantes : marine pour la structure, turquoise pour ce qui est validé, corail pour un risque ou une action prioritaire.
- Les photos montrent la culture et l’usage métier ; elles n’illustrent jamais de faux résultats techniques.
- Tous les exemples et métriques restent strictement ceux du dépôt : 7 586 événements, 14 903 passages, 59 tests, CHIMERE à 10 273 caractères et scores RAGAS observés.

## Vérification

- Le deck reste à 12 slides, avec des notes présentateur complètes.
- Chaque slide est rendue et vérifiée pour les débordements, la lisibilité et les alignements.
- La fidélité au gabarit existant est contrôlée.
- Les tests du dépôt et la démo Docker sont rejoués avant livraison.
