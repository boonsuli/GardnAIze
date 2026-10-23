# Vision : organisation de l'inférence Deep Learning

Ce dossier prépare l'intégration future des modèles de vision au service FastAPI, **sans modifier les routes actuelles**.

## Responsabilités prévues

- `preprocessing` : décodage sûr, validation de format et dimensions, normalisation identique à l'entraînement.
- `inference` : chargement d'un modèle `.keras` versionné, prédiction et probabilités.
- `schemas` : contrats d'entrée/sortie et taxonomie des classes.
- `monitoring` : durée d'inférence, version, erreurs, sans journaliser les photos.

Deux expériences distinctes sont initialisées dans `notebooks/` : espèces végétales et scènes de jardins. Aucun modèle n'est encore entraîné ou branché à l'API. Avant déploiement : ajouter tests, limites de taille, vérification du type MIME, checksum et provenance des poids, métriques sur test indépendant et intégration Docker.
