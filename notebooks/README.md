# Notebooks IA GardnAIze

- `01_plant_images_dl.ipynb` : classification de plantes à partir de photos étiquetées.
- `02_garden_scenes_dl.ipynb` : classification de scènes de jardins, avec étiquettes à définir selon le corpus retenu.

Ces deux notebooks sont des **points de départ non exécutés**, sans datasets intégrés ni résultats mesurés. Exécuter depuis `notebooks/` avec un environnement Python 3.12 comprenant `tensorflow`, `numpy`, `pandas`, `matplotlib` et `scikit-learn`. Configurer `DATASET_DIR` pour chaque corpus. Les notebooks incluent une séparation train/validation exploratoire ; ajouter un jeu de test indépendant et une comparaison MobileNetV2 avant toute revendication de validation du bloc 5.

L'objectif prioritaire est de choisir des datasets documentés, annotés et légalement réutilisables. Ne pas ajouter de grandes images ni de poids de modèles au dépôt.
