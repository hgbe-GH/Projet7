# Supports de soutenance

Le contenu commun des 12 slides et des notes est dans `contenu_support.py`.
Le fil conducteur est une bibliothèque : catalogue, passages, sens, bibliothécaire,
rédacteur, guichet, puis contrôle des réponses. Les termes techniques et les
limites de l’analogie sont explicités dans chaque fiche.
Les fichiers générés sont versionnés dans `outputs/` pour être immédiatement consultables.

Depuis la racine du dépôt :

```sh
python docs/soutenance/generer_support.py
python docs/soutenance/generer_annexe.py
python scripts/lancer_soutenance.py
```

La première commande génère le diaporama, le guide, le démonstrateur, le contenu
JSON et les deux conducteurs Markdown. La seconde demande Graphviz (`dot`) et
recrée le diagramme UML et l’autoévaluation. Le lanceur démarre Docker et le serveur des pages en arrière-plan, qui reste
accessible après fermeture du terminal. Le serveur local permet la démo
avec le proxy vers FastAPI, sur le port 8000. Ouvrir `http://127.0.0.1:8765`.

Le démonstrateur embarque la répétition du jour depuis
`outputs/demo/demo_api_2026-10-01.json`. Son mode enregistré ne fait aucun appel
réseau ; son mode direct appelle réellement `/ask`. Le guide reste hors partage.

`generer_pptx.mjs` reprend les 12 slides du template original fourni et les
modifications décrites dans `template-frame-map.json`, puis ajoute les notes
depuis `outputs/contenu-soutenance.json`. Son exécution demande Node et le SDK
`@oai/artifact-tool` (version indiquée dans `package.json`) fourni par le runtime
de création de présentations. Le PowerPoint final est déjà livré ; ce SDK
n’est pas une dépendance du moteur RAG ni de la présentation HTML.

Le rapport Word est généré avec `python scripts/build_report.py` dans
l’environnement Conda du projet. Les PDF sont des exports vérifiés des
supports HTML et Word. `assembler_livrables.py` prépare le ZIP de dépôt et
le kit de préparation, avec contrôle de non-inclusion de la clé API.

Le document de mission contient aussi des exercices de cours : la soutenance
porte sur la mission Puls-Events. Les consignes y sont une source des critères
à vérifier ; elles ne déclenchent pas automatiquement d’action sur un compte
ou un service externe.
