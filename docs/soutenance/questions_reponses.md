# Questions et réponses — soutenance du 1er octobre 2026

## Pourquoi le RAG, et avez-vous entraîné le modèle ?

Le RAG ajoute les passages du catalogue au moment de la question. Je n'ai ni entraîné ni ajusté Mistral ; j'ai construit un index et un prompt.

Les données peuvent évoluer sans réentraîner le modèle : on recollecte puis on réindexe. Le RAG ne supprime pas les erreurs de génération.

Preuve : rag.py : answer_question()

## Pourquoi Mistral et ces deux modèles ?

Mistral est demandé par le brief. mistral-embed sert à rechercher. Le POC évalué utilisait mistral-small-latest ; la démo utilise ministral-8b-2512 car Small était limité aujourd’hui.

Le modèle alternatif a réussi les deux scénarios API réels. Ce n’est pas un benchmark comparatif et les scores RAGAS de juillet restent ceux de Small. Comme les embeddings n’ont pas changé, aucun réindexage n’est nécessaire. Le nom de version est fixé pour cette démo.

Preuve : settings.py ; rag.py ; indexing.py

## Pourquoi FAISS et quel index utilisez-vous ?

FAISS permet une recherche vectorielle locale sans serveur supplémentaire. L'index livré est IndexFlatL2, une recherche exacte par distance euclidienne au carré.

Il contient 14 903 vecteurs de 1 024 dimensions. Les dimensions ne sont pas des catégories nommées. Pour beaucoup plus de données, il faudrait mesurer les coûts de mémoire et de recherche avant de choisir un index approximatif ou une base serveur. Le code n'applique pas de normalisation explicite pour une recherche cosine.

Preuve : seed-data/index/faiss/index.faiss ; indexing.py

## Pourquoi 1 000 caractères, 200 de chevauchement et top-k 4 ?

Ce sont les réglages de départ du POC : des passages assez courts, un chevauchement pour les frontières et quatre contextes pour limiter le bruit.

Ils n'ont pas été prouvés optimaux. Je comparerais plusieurs tailles et valeurs de k en mesurant le rappel des événements attendus, la fidélité, la latence et le coût. RecursiveCharacterTextSplitter respecte les séparateurs ; ce n'est pas une découpe fixe tous les 800 caractères.

Preuve : index_manifest.json ; settings.py

## Vos événements sont-ils encore récents et à venir ?

Le seed couvre la première date du 10 juillet 2025 au 10 juillet 2026. C'était le périmètre construit en juillet ; il n'est pas maintenu à jour au 1er octobre.

Certains événements ont maintenant plus d'un an, et la borne haute exclut les nouveaux événements qui commencent après juillet. Quelques événements récurrents se prolongent après la borne. Pour remplir durablement le besoin d'événements à venir, il faut une collecte planifiée avec un horizon futur et un filtrage des occurrences au moment de la réponse. Je reconnais cet écart actuel.

Preuve : fetch_manifest.json ; ingestion.py : build_records_where_clause()

## Pourquoi Opendatasoft plutôt que l'API native OpenAgenda ?

La mission renvoie au dataset public OpenAgenda d'Opendatasoft ; c'est cette source qui est utilisée et documentée.

La collecte est sans clé sur cette source. Elle normalise un schéma qui pourrait être alimenté par une autre source. Je ne prétends pas utiliser les endpoints natifs OpenAgenda.

Preuve : ingestion.py : OpenAgendaClient

## Comment évitez-vous les hallucinations ?

Le prompt impose le contexte et le refus si l'information manque ; les sources permettent un contrôle. Cela réduit le risque sans garantir zéro erreur.

Je compléterais par des filtres explicites, un seuil calibré, un contrôle des faits, des tests adverses et une revue humaine. Les descriptions externes doivent aussi être traitées comme des données non fiables pour éviter les injections de prompt.

Preuve : rag.py : SYSTEM_PROMPT

## Pourquoi Lyon retourne-t-il quand même des sources ?

Le top-k renvoie les voisins les plus proches, même si leur ville ne correspond pas. Ce sont des documents récupérés, pas forcément des recommandations.

Le refus Lyon observé vient du modèle lisant le contexte Paris. Il n'existe pas de blocage géographique codé ni de seuil. Un filtre ville ou un rejet mesuré rendrait le comportement plus fiable et pourrait éviter un appel de génération inutile.

Preuve : rag.py : build_retriever(), build_source_entries()

## Que signifient 0,900 et 1,000 ?

0,900 mesure la fidélité au contexte sur trois cas. 1,000 mesure la précision et le classement des contextes par RAGAS, pas la récupération de tous les événements pertinents.

Ce ne sont ni une satisfaction de 90 % ni une exactitude universelle de 100 %. Il manque une mesure explicite de rappel du retrieval et un échantillon plus large. Les résultats datent du 23 juillet et peuvent varier avec le juge.

Preuve : ragas_results.json ; ragas_evaluation.py

## Pourquoi la correction n'est-elle que 0,683 ?

Une réponse peut être soutenue par un contexte mais s'écarter de la référence, oublier une information ou ajouter un détail fragile.

Je relis les cas plutôt que de déduire une cause unique du score. Le cas famille obtient environ 0,581 en correction : des horaires sont généralisés à plusieurs visites. Les références doivent être enrichies lorsque nécessaire, et les réponses doivent mieux distinguer les faits sourcés des conseils.

Preuve : rapport, section 7 ; ragas_results.json

## Quatre cas corrects : votre précision est-elle de 100 % ?

Non. Ce classement porte sur quatre exemples et sur une règle locale qui accepte un titre présent dans la réponse ou dans les sources.

La similarité locale est lexicale avec SequenceMatcher, pas sémantique. L'exact match est nul dans la sortie enregistrée malgré quatre classements corrects. Cette évaluation vérifie surtout des repères ; elle doit être complétée par les faits, les dates, le refus et des annotations plus nombreuses.

Preuve : evaluation.py : classify_result(), match_expected_titles()

## Pourquoi seulement trois exemples RAGAS ?

Ils démontrent une évaluation réellement exécutée avec les contextes exacts. Ils sont insuffisants pour conclure statistiquement.

J'ajouterais villes, catégories, dates, questions ambiguës, négations, hors corpus et paraphrases. Je séparerais les cas utilisés pour choisir les réglages de ceux utilisés pour les évaluer et j'intégrerais une revue humaine indépendante du juge.

Preuve : tests/fixtures/ragas_eval_dataset.csv

## Les 76 tests appellent-ils réellement Mistral ?

La suite de tests utilise des doublures pour vérifier le code sans dépendre du réseau. La démo API et l'évaluation enregistrée font les appels réels séparément.

Les tests ne prouvent ni la disponibilité du fournisseur ni la qualité de toutes les réponses. Les appels réels ont été vérifiés séparément aujourd’hui. Dix-sept régressions supplémentaires couvrent les erreurs fournisseur, l’arrêt des répétitions et la gestion des dates dans le contexte.

Preuve : tests/conftest.py ; test_rag.py ; test_api.py

## Est-ce réellement hors ligne ?

Non. Le corpus et FAISS sont locaux, mais Mistral est appelé pour l'embedding de la question et la génération.

Les pages et les résultats enregistrés fonctionnent hors ligne ; ils ne remplacent pas un RAG live. Une version entièrement locale demanderait des modèles locaux compatibles et un nouvel index si l'embedding change.

Preuve : rag.py ; indexing.py : _build_embeddings()

## Que fait /rebuild exactement ?

Il relit le Parquet, redécoupe, recalcule les embeddings et remplace l'index. Il invalide ensuite le retriever et le client de chat.

Il ne télécharge pas de nouveaux événements. Pour actualiser les données il faut d'abord fetch_events.py, puis l'indexation. Cela peut coûter et durer ; je ne le lance pas pendant la soutenance. En production, une reconstruction dans un dossier séparé puis une bascule atomique éviterait les conflits.

Preuve : service.py : rebuild() ; indexing.py : rebuild_index_artifacts()

## Comment protégez-vous la clé et les endpoints ?

La clé est dans l'environnement ou .env ignoré par Git. Docker ne la copie pas. /rebuild dispose d'un jeton optionnel.

Le jeton n'est pas obligatoire dans le POC ; avant exposition il faut l'activer, ajouter authentification et limites d'appels. Les erreurs fournisseur sont déjà filtrées. L'index pickle doit provenir d'une source de confiance. Je montre .env.example, jamais .env.

Preuve : .gitignore ; .dockerignore ; api.py

## Que garantit Docker et /health ?

Docker fournit le code, les dépendances et un seed dans un environnement commun. /health confirme que le serveur répond et expose sa configuration.

Health ne prouve pas que la clé fonctionne ni que l'index est chargé. Le chargement est paresseux à la première question. Le volume conserve l'index de travail. Une readiness complète devrait vérifier le corpus et un contrôle adapté du fournisseur, sans appels coûteux à chaque sondage.

Preuve : Dockerfile ; docker_entrypoint.sh ; service.py : health()

## Comment avez-vous débloqué Mistral ?

J’ai isolé les appels : les embeddings fonctionnaient, la génération avec Small renvoyait 429. Ministral 8B répondait ; je l’ai configuré puis vérifié les deux scénarios RAG.

La clé était valide et identique dans Docker. L’accès aux limites administratives n’était pas autorisé avec cette clé : la limite précise n’est pas connue. L’API traite désormais les erreurs fournisseur sans exposer leurs détails ; le script de démo ne relance plus 60 fois les appels. Il faudra réévaluer le modèle alternatif et surveiller les limites par modèle.

Preuve : Vérification du 1er octobre ; api.py : gestion des exceptions

## Avez-vous une CI/CD et mesuré la montée en charge ?

Non. Les scripts et les tests sont livrés ; aucune pipeline CI/CD ni benchmark de charge n'est implémenté.

Je proposerais tests sans secret à chaque push, construction Docker, contrôles de disponibilité, puis déploiement contrôlé. Je mesurerais p50/p95, débit, taux d'erreur, coûts et ressources sur une charge représentative. Une démo courte ne permet pas de les extrapoler.

Preuve : tests/ ; Dockerfile ; README.md

## Quel est le coût et la valeur pour Puls-Events ?

La valeur attendue est une découverte plus naturelle avec des sources vérifiables. Elle n'a pas encore été mesurée auprès d'utilisateurs.

Coût = embeddings de construction et mise à jour + embedding par question + tokens de génération, et éventuellement juge RAGAS. Je ne donne pas de prix non vérifié. Un pilote comparerait satisfaction, clic vers source, refus correct, latence et coût par demande à une recherche classique.

Preuve : Perspectives du README et du rapport

## Comment comparer un nouveau modèle d'embedding ?

Je reconstruis l'index avec ce modèle et j'utilise le même modèle pour les questions. On ne peut pas mélanger deux espaces vectoriels.

Même si les deux vecteurs ont la même dimension, leurs coordonnées ne sont pas forcément comparables. Je garde le même corpus et jeu d'évaluation pour comparer rappel, pertinence, coût et latence. Le manifeste trace le modèle utilisé.

Preuve : index_manifest.json ; service.py ; settings.py

## Comment rendre le système plus utile pour des dates et lieux précis ?

J'ajouterais des contraintes métier explicites sur la ville et les occurrences, en complément de la recherche sémantique.

Un événement récurrent ne doit pas être interprété comme une disponibilité continue entre first_timing et last_timing. Le corpus brut conserve timings ; le POC utilise surtout première et dernière dates. Un futur moteur doit sélectionner l'occurrence qui correspond à la demande et vérifier accessibilité, tarifs et public lorsque les données existent.

Preuve : ingestion.py : _extract_timings() ; métadonnées de FAISS
