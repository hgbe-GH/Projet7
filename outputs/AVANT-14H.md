# Ta préparation pour 14 h

La démo directe est rétablie. Docker et le serveur des supports sont lancés.
Les deux questions ont réussi avec `ministral-8b-2512` en 4,773 s au total.
Les 76 tests locaux passent. Il reste à comprendre, répéter et préparer ton partage.

1. **15 minutes : comprendre.** Ouvre [le guide personnel](http://127.0.0.1:8765/guide-soutenance-openagenda-rag.html#comprendre). Lis le principe RAG, le parcours des données et le glossaire. Explique ensuite sans lire : « rechercher des passages, les donner au modèle, rédiger une réponse sourcée ».
2. **25 minutes : lire le conducteur.** Lis les 12 étapes avec leurs explications simples. Le texte « À lire » est ton script ; les détails servent aux questions. Tu peux activer « Afficher seulement le script oral » pendant l'entretien.
3. **15 minutes : pratiquer la démo.** Ouvre [le démonstrateur](http://127.0.0.1:8765/demo-soutenance.html), vérifie `/health`, lance Concert Fishers en direct et contrôle le lieu, la date et l’URL dans les sources. Ce concert est passé. Lance ensuite Lyon : le corpus Paris ne permet pas de répondre. Les sources récupérées ne sont pas toutes des recommandations. Un conseil général hors contexte reste possible : reconnais-le si présent.
4. **15 minutes : préparer les questions.** Dans le guide, lis les réponses sur les modèles, FAISS, top-k, la fraîcheur du corpus, RAGAS, les limites et `/rebuild`.
5. **15 minutes : répéter avec les gestes.** Ouvre [le diaporama](http://127.0.0.1:8765/presentation-soutenance-openagenda-rag.html), démarre son chronomètre et présente les 12 slides. La démo est dans la slide 8. La fin inclut une visite courte du rapport et du dépôt. Vise 15 minutes, puis corrige ce qui fait perdre le fil.
6. **Avant 13 h 30 : préparer les fenêtres.** Une fenêtre avec diaporama, démo et [Swagger](http://127.0.0.1:8000/docs) ; une autre avec le guide personnel. Ouvre le rapport technique et le dépôt. Garde les PDF accessibles en secours. Le guide doit rester hors partage.
7. **À 13 h 45 : te connecter et vérifier.** Son, caméra, lien de soutenance, alimentation, partage de la bonne fenêtre, chronomètre remis à zéro. Garde Docker et le serveur local ouverts. Si nécessaire, vérifie une fois `/health` ; évite les appels répétés.

## Les faits à retenir

- **Mission :** prototype de recommandation culturelle pour Puls-Events ; Jérémy joue le responsable technique. Ce sont les livrables de cette mission que tu présentes.
- **Données :** 7 586 événements de Paris, 14 903 passages, vecteurs de 1 024 dimensions. Collecte du 10 juillet : corpus figé, à actualiser pour les sorties d’aujourd’hui.
- **Recherche :** chunks de 1 000 caractères, chevauchement maximal de 200 ; FAISS `IndexFlatL2` ; quatre passages récupérés, pas nécessairement quatre événements.
- **Modèles :** `mistral-embed` transforme textes et question en vecteurs. `ministral-8b-2512` rédige la démo ; il remplace `mistral-small-latest`, limité en 429. Tu n’as pas entraîné le modèle. L’index n’a pas été reconstruit car l’embedding reste identique.
- **Preuves :** 76 tests vérifient le code avec des doublures. Deux appels réels sont vérifiés séparément. RAGAS de juillet : fidélité 0,900 ; pertinence 0,846 ; précision du contexte 1,000 ; correction 0,683 sur seulement trois cas. Ces scores concernent l’ancien modèle.
- **API :** `/health` vérifie le serveur et sa configuration ; `/ask` exécute le RAG ; `/rebuild` relit le Parquet et reconstruit l’index, sans recollecter. Ne lance pas de reconstruction pendant la soutenance.

## Ton début, à lire

« Bonjour Jérémy. Pour expliquer ce POC, je vous propose une image simple : une bibliothèque d'événements culturels. Un visiteur arrive avec une demande, par exemple une sortie en famille à Paris. Il souhaite une réponse utile et des informations qu'il peut vérifier. Mon travail a été de constituer le catalogue, de préparer ses fiches pour la recherche, puis de relier cette recherche à un modèle qui rédige et à une API que vos équipes peuvent appeler. Le catalogue livré contient 7 586 événements parisiens. Je vais suivre ce parcours avec vous, montrer deux demandes en direct et expliquer ce qui fonctionne ainsi que ce qui reste à améliorer. »

## Le déroulé

15 minutes de présentation : mission → RAG → données → découpage et embeddings → recherche et génération → préparation de l’index → API et Docker → démo → tests → RAGAS → limites → conclusion, rapport et dépôt.
Ensuite : 10 minutes de discussion, puis 5 minutes de débrief.

Pour le rapport, utilise `outputs/rapport-technique-openagenda-rag.pdf` et l’actualisation du README local. Dans le dépôt, montre rapidement `scripts/`, `src/`, `tests/` et `seed-data/`.
Les correctifs et supports du jour sont destinés au dépôt GitHub. Le dépôt sur la plateforme OpenClassrooms reste à faire. Le kit ZIP inclut les supports et le code actuel sans la clé API.

## Si un problème revient

Annonce l’échec. Le bouton « Réponse enregistrée » montre explicitement la répétition du jour ; il ne remplace pas automatiquement un appel réel. Si le navigateur tombe, utilise le PDF du diaporama et le script oral PDF. Si tu perds le fil : catalogue → passages → sens → bibliothécaire → rédacteur → guichet → contrôle.

Après une fermeture, depuis la racine du projet :

```sh
python scripts/lancer_soutenance.py
```
