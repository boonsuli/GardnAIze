# GardnAIze — Notebooks de vision et validation

Ce dossier est consacré aux **images** et aux expérimentations de classification/validation visuelle. Il ne constitue pas le pipeline d'ingestion des caractéristiques botaniques.

## Inventaire réel
- `01_verify_ml_database.ipynb` : vérification des données et de la base ML.
- `02_plant_images_dl.ipynb` : classification supervisée d'images de plantes (TensorFlow).
- `03_garden_scenes_dl.ipynb` : classification de scènes de jardins.
- `04_explore_garden_images.ipynb` : exploration des images de jardins.
- `05_train_garden_classifier.ipynb` : entraînement du classifieur de jardin.
- `06_evaluate_garden_classifier.ipynb` : évaluation du classifieur.
- `07_review_garden_images.ipynb` : revue et contrôle des images.

## Distinction des autres notebooks
- `ai-service/notebooks/` : comparaison d'algorithmes ML (K-Means, voisins, Random Forest) sur caractéristiques tabulaires.
- `ai-service/plant-ingestion/` : acquisition d'exports **autorisés**, normalisation, rapprochement des noms scientifiques et consolidation CSV/JSON.

Les trois familles sont complémentaires. Ne pas interpréter un cluster K-Means comme une propriété botanique vérifiée. Ne pas utiliser une prédiction visuelle comme preuve de rusticité, d'exposition ou de tolérance à la sécheresse.

## Exécution et qualité
Ces notebooks nécessitent des datasets d'images locaux légalement réutilisables, avec licences et provenance documentées. Vérifier les chemins, les dépendances, les splits et les métriques avant toute annonce de résultat. Aucun nouveau résultat d'entraînement n'est revendiqué par cette documentation.
