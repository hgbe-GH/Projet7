# Questions et réponses préparées pour la soutenance

## 1. Pourquoi utiliser un RAG plutôt qu'un LLM seul ?

Un LLM seul ne connaît pas nécessairement les événements du corpus et peut en
inventer. Le RAG récupère d'abord des événements réels, puis contraint la
génération avec ce contexte. Les sources retournées rendent aussi la réponse
vérifiable.

## 2. Pourquoi FAISS ?

FAISS offre une recherche vectorielle rapide, locale et simple à persister. Il
convient au volume du POC et évite d'ajouter un service de base de données. Pour
une production distribuée avec filtres complexes, une base vectorielle serveur
pourrait devenir plus adaptée.

## 3. Pourquoi Mistral pour les embeddings et le chat ?

Le brief demande Mistral et l'écosystème LangChain fournit des intégrations
directes. `mistral-embed` est spécialisé dans la représentation sémantique ;
`mistral-small-latest` offre un compromis coût-latence-qualité cohérent avec un
POC et un compte gratuit.

## 4. Pourquoi découper un événement en plusieurs chunks ?

Certaines descriptions dépassent la taille utile d'un document de recherche.
Des chunks de 1 000 caractères avec 200 caractères de chevauchement évitent de
perdre une information située à une frontière. Les métadonnées permettent de
regrouper ensuite les chunks d'un même événement.

## 5. Comment vérifiez-vous que tous les événements sont indexés ?

Le manifeste d'index indique le nombre d'événements et de documents. Le parquet
`indexed_documents.parquet` permet une inspection humaine. Les tests vérifient
le schéma, les métadonnées, les vecteurs non vides, la persistance et le
rechargement de l'index.

## 6. Que signifie une fidélité RAGAS de 0,900 ?

Sur ce petit jeu de trois cas, les réponses sont fortement soutenues par les
contextes réellement transmis au modèle. Ce bon score ne suffit pas à prouver
la qualité globale : la correction moyenne par rapport aux références humaines
est de 0,683. Il faut donc surtout mieux cadrer la précision et la sélection des
informations attendues.

## 7. Pourquoi seulement trois exemples RAGAS ?

Trois exemples répondent à l'objectif de soutenance et démontrent un pipeline
réel, reproductible et documenté. Ce volume ne suffit pas pour conclure
statistiquement. Une étape produit doit élargir le jeu par catégories, villes,
saisons, cas négatifs et formulations ambiguës.

## 8. Comment gérez-vous une question hors corpus ?

Le prompt demande au modèle de dire qu'il ne sait pas lorsque le contexte ne
contient pas l'information. La démo Lyon illustre ce comportement. Une version
plus robuste ajouterait un seuil de distance vectorielle avant l'appel au LLM.

## 9. Pourquoi le cas limite retourne-t-il quand même des sources ?

Le retriever renvoie toujours les voisins les plus proches, même s'ils sont peu
pertinents. Le LLM constate ensuite qu'ils ne répondent pas à la question. En
production, un seuil de similarité permettrait de retourner zéro source et de
rejeter la demande plus tôt.

## 10. Comment protégez-vous les secrets ?

La clé Mistral est placée dans `.env`, ignoré par Git, ou injectée par variable
d'environnement dans Docker. `.env.example` ne contient aucune valeur réelle.
L'image Docker ne copie pas la clé. Le jeton optionnel `API_REBUILD_TOKEN`
protège l'endpoint de reconstruction.

## 11. Pourquoi conserver le retriever et le modèle en mémoire ?

Le chargement de l'index et l'initialisation du modèle ont un coût. Le service
les instancie une fois puis les réutilise, ce qui réduit la latence de `/ask`.
Après `/rebuild`, ces objets sont invalidés pour forcer un rechargement propre.

## 12. Comment le projet reste-t-il reproductible ?

Les versions sont figées dans `requirements.txt` et reprises par
`environment.yml`. Les scripts de collecte et d'indexation produisent des
manifestes. Les tests sont isolés du réseau, tandis que les validations
d'intégration avec Mistral sont explicitement documentées.

## 13. Quelle serait la première amélioration métier ?

Élargir le corpus à plusieurs villes et construire avec les équipes métier un
jeu annoté plus représentatif des intentions utilisateur. Cela permettrait de
mesurer la couverture réelle avant d'optimiser davantage les modèles.

## 14. Le système est-il prêt pour la production ?

Non, c'est un POC fonctionnel. Il démontre la chaîne technique et sa valeur. Une
mise en production nécessiterait authentification, supervision, gestion des
quotas, collecte planifiée, tests de charge, politique de conservation des
données, jeu d'évaluation étendu et stratégie de reprise.
