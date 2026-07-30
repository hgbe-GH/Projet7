# Conception du guide intégral de soutenance

## Objectif

Transformer le guide HTML en une grande antisèche couvrant l’intégralité de la soutenance de 30 minutes. Le
PowerPoint reste composé de 12 slides simples. Le HTML devient le support personnel détaillé que le candidat peut
lire presque mot pour mot, tout en comprenant ce qu’il présente et pourquoi.

## Périmètre

Le guide couvre :

1. la préparation matérielle et technique avant l’appel ;
2. l’ouverture de la soutenance et les 12 slides ;
3. la démonstration live de l’API ;
4. le parcours du rapport technique et du dépôt GitHub ;
5. les transitions et la gestion du temps ;
6. la discussion de 10 minutes avec le jury ;
7. les plans de secours en cas de problème ;
8. la conclusion et le débrief.

Le PowerPoint et le code du projet ne sont pas modifiés.

## Structure du script oral

Le script principal est calibré pour environ 15 minutes. Pour chaque slide, le guide contient :

- la durée visée ;
- l’objectif de la slide ;
- les actions à réaliser avant de parler ;
- un texte oral intégral à la première personne ;
- le moment précis où changer de slide ;
- les éléments visuels à pointer ;
- une transition complète vers la suite ;
- une version courte de secours si le temps manque.

Le texte oral principal est visuellement distinct afin de pouvoir être lu rapidement pendant la soutenance.

## Antisèche technique par slide

Chaque slide conserve les neuf repères pédagogiques :

- Ce que je cherche à démontrer
- Ce qui entre
- Ce que mon code fait
- Ce qui sort
- Pourquoi ce choix
- Ce que je dis
- Ce que je montre
- À ne pas dire
- Question probable

Ces repères sont enrichis par :

- une explication en langage simple ;
- le vocabulaire technique à connaître ;
- la justification des paramètres importants ;
- les limites honnêtes du POC ;
- une réponse courte et une réponse développée à la question probable.

## Démonstration live

La démonstration dispose d’un conducteur autonome :

- vérifications cinq minutes avant la soutenance ;
- commande à lancer et résultat attendu ;
- phrases exactes à prononcer pendant l’attente ;
- scénario nominal sur Paris ;
- scénario hors périmètre sur Lyon ;
- points à montrer dans la réponse JSON ;
- lien explicite entre la démo et les exigences métier ;
- conduite à tenir si Docker, l’API ou Mistral ne répond pas ;
- version de secours avec résultats déjà enregistrés.

Le guide précise que le candidat ne doit jamais afficher le fichier `.env` ni la clé Mistral.

## Rapport et dépôt

Une section fournit un parcours oral minute par minute :

- quoi ouvrir ;
- quels dossiers ou fichiers montrer ;
- ce qu’ils prouvent ;
- ce qu’il est inutile de détailler spontanément ;
- comment revenir au fil de la présentation si l’évaluateur demande du code.

## Questions-réponses

Les questions sont organisées selon les thèmes annoncés dans le format de soutenance :

- modèles et architecture ;
- données, embeddings et recherche ;
- évaluation et métriques ;
- limites ;
- reproductibilité et industrialisation ;
- sécurité et exploitation ;
- usage métier.

Chaque réponse comporte :

1. une réponse directe de 15 à 25 secondes ;
2. une explication développée si le jury insiste ;
3. une formulation à éviter ;
4. lorsque c’est pertinent, l’amélioration recommandée.

## Navigation et lisibilité

Le HTML reste autonome, imprimable et lisible sur ordinateur ou téléphone. Le sommaire permet d’atteindre
rapidement :

- chaque slide ;
- la démo ;
- le dépôt et le rapport ;
- les questions ;
- les plans de secours.

La mise en page distingue clairement :

- **À lire** : texte oral principal ;
- **À faire** : manipulation ou changement d’écran ;
- **À comprendre** : explication technique ;
- **En cas de question** : réponse prête à l’emploi ;
- **En cas de problème** : plan de secours.

## Critères de réussite

- Le guide contient exactement 12 fiches correspondant aux 12 slides.
- Le script oral principal est calibré pour environ 15 minutes.
- La totalité des 30 minutes de soutenance est couverte.
- La démo est expliquée pas à pas avec texte oral et plans de secours.
- Le rapport et le dépôt disposent de leur propre script.
- Les neuf repères pédagogiques sont présents pour chaque slide.
- Les chiffres et paramètres du projet restent exacts.
- Le HTML est valide, sans erreur navigateur ni débordement horizontal.
- Le PowerPoint reste inchangé.
