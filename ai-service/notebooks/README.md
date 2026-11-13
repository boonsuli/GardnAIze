# GardnAIze — Recherche et comparaison d'algorithmes ML

Ces six notebooks expérimentent les algorithmes sur des caractéristiques tabulaires ; **ils ne collectent pas de données fournisseurs**.

## Inventaire
1. `01_data_audit.ipynb` — audit et valeurs manquantes (démo synthétique).
2. `02_clustering_model_search.ipynb` — K-Means, clustering hiérarchique, DBSCAN.
3. `03_dimension_reduction.ipynb` — PCA et visualisation.
4. `04_recommendation_model_search.ipynb` — comparaison de métriques de voisinage.
5. `05_supervised_target_search.ipynb` — comparaison supervisée dont Random Forest.
6. `06_selection_report.ipynb` — synthèse et limites des résultats.

## Articulation avec les autres dossiers
- `../plant-ingestion/` : notebooks numérotés d'ingestion par famille de source et consolidation des CSV/JSON.
- `../../notebooks/` : classification/validation **d'images** de plantes et jardins.
- `../../database/migrations/ml/V1__create_horticulture_reference_and_plants.sql` : schéma horticole existant, à préserver.

**Pas de doublon à supprimer** : l'audit ML examine les caractéristiques d'un dataset, alors que la consolidation d'ingestion rapproche des enregistrements provenant de plusieurs sources. Les deux étapes peuvent mesurer les doublons, mais avec des objectifs différents.

## Règles scientifiques
Les données synthétiques ne sont pas des faits botaniques. Pour KNN supervisé, des catégories fiables et étiquetées sont indispensables ; le notebook de recherche de voisinage n'est pas une preuve d'un classifieur KNN déjà entraîné. Entraîner et évaluer les modèles sur un catalogue consolidé commun, avec séparation anti-fuite entre apprentissage et test. K-Means produit des clusters, pas des catégories validées. Le matching Random Forest nécessite des exemples jardin–plante labellisés.

Ne pas écraser des attributs vérifiés par des valeurs prédites. La complétude et la qualité des données conditionnent l'admissibilité au matching.
