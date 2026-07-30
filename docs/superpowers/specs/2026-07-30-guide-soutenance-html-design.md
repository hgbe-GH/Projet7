# Guide HTML de soutenance - conception

## Objectif

Créer un guide autonome que Hugo peut ouvrir localement et utiliser comme conducteur pendant sa dernière heure de préparation. Le document ne remplace pas le PowerPoint déjà déposé. Il transforme les supports existants en une prestation orale maîtrisée, à la première personne, conforme au format OpenClassrooms.

## Public et résultat attendu

Le guide est destiné uniquement au candidat. À la fin de sa lecture et d'une répétition, il doit pouvoir :

- présenter le POC en 12 à 15 minutes ;
- exécuter la démonstration sans hésitation ;
- montrer rapidement le rapport et la structure du dépôt ;
- expliquer les choix techniques avec des mots simples ;
- répondre aux questions probables de « Jérémy » ;
- reconnaître honnêtement les limites du POC sans dévaloriser le travail.

## Format

Un fichier HTML unique, sans dépendance réseau, placé dans `outputs/` à côté du PowerPoint et du rapport. Le document doit rester lisible dans un navigateur et à l'impression.

La page comprend :

1. un tableau de bord de dernière minute avec l'état vérifié du projet ;
2. une checklist avant connexion à la soutenance ;
3. un conducteur oral chronométré de 15 minutes ;
4. pour chaque étape :
   - « Ce que je dis », rédigé à la première personne ;
   - « Ce que je fais », avec les manipulations à l'écran ;
   - « Ce que je dois comprendre », sous forme de notes candidat ;
   - une transition vers l'étape suivante ;
5. une procédure de démonstration nominale et hors périmètre ;
6. un parcours rapide du rapport et du dépôt GitHub ;
7. une fiche d'explication des notions RAG, embeddings, FAISS, chunks, FastAPI, Docker et RAGAS ;
8. un jury blanc couvrant les cinq axes annoncés par OpenClassrooms ;
9. les questions difficiles spécifiques au projet :
   - corpus figé et fraîcheur des événements ;
   - quatre cas annotés contre trois cas RAGAS ;
   - absence de seuil de similarité ;
   - choix de `top_k=4`, des chunks 1000/200 et de FAISS ;
   - dépendance à l'API Mistral ;
   - validité statistique limitée de l'évaluation ;
   - sécurité de `/rebuild` et passage en production ;
10. des réponses de secours en cas de problème de démo ;
11. une checklist finale de cinq minutes.

## Déroulé oral cible

- 0:00-2:20 : contexte, besoin métier et explication simple du RAG ;
- 2:20-6:30 : données, architecture, embeddings, FAISS et API ;
- 6:30-8:50 : Docker et démonstration live ;
- 8:50-10:10 : rapport technique et structure du dépôt ;
- 10:10-13:10 : méthode d'évaluation et résultats ;
- 13:10-15:00 : limites, améliorations et conclusion.

Ce découpage conserve les 15 diapositives mais ajoute explicitement le rapport et le dépôt, deux éléments demandés dans le déroulé officiel.

## Ton et niveau de détail

Le texte oral utilise des phrases naturelles et courtes. Il évite de réciter du code. Les notes techniques sont plus détaillées, mais restent séparées du discours afin que Hugo sache ce qu'il doit dire et ce qu'il doit seulement comprendre.

Les réponses du jury suivent une structure constante :

1. réponse directe ;
2. justification par un élément réel du projet ;
3. limite reconnue ;
4. amélioration de production.

## Comportement hors ligne

Le HTML ne charge aucune police, bibliothèque ou ressource distante. Les liens vers les livrables utilisent des chemins relatifs. Les commandes sont copiables. Une version imprimée conserve les titres, les blocs et la lisibilité.

## Contrôles

Avant livraison :

- vérifier que tous les faits correspondent aux fichiers du projet ;
- confirmer les résultats frais : 59 tests, API saine et démo fonctionnelle ;
- vérifier l'absence de texte provisoire ;
- ouvrir le HTML dans un navigateur ;
- contrôler les liens locaux et la lisibilité ;
- vérifier que les commandes ne dévoilent aucun secret ;
- vérifier que le conducteur couvre les 15 minutes et les cinq axes du jury.
