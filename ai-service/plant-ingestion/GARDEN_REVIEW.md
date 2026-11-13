# Revue locale des jardins — PR #30

1. Installer `ipywidgets`, `ipython` et `jupyterlab` dans l'environnement notebook.
2. Déposer uniquement des images autorisées dans `inputs/images/` (ignorées par Git).
3. Copier `inputs/garden_manifest.example.csv` vers `inputs/garden_manifest.csv`.
4. Compléter une ligne par photo: `source_key,external_id,image_path,garden_group_key,license_name,redistribution_allowed,climate_zone,soil_type,exposure`. Utiliser un chemin sous `inputs/images/`; `garden_group_key` identifie le jardin physique, commun à toutes ses photos.
5. Depuis `ai-service/plant-ingestion/`, ouvrir `005_garden_visual_review.ipynb` et exécuter les cellules. Choisir ACCEPTED/REJECTED/UNCERTAIN puis **Enregistrer et suivante**. Les décisions sont sauvegardées immédiatement dans `outputs/garden_reviews.csv`.
6. Exécuter la cellule d'export vers `outputs/gardens_reviewed.json`. Les splits TRAIN/VAL/TEST (70/15/15 en moyenne) sont déterministes **par jardin**. Sur de petits échantillons les proportions exactes peuvent différer.
7. Appliquer Flyway ML V5 puis lancer `python database/scripts/import_garden_reviews.py ai-service/plant-ingestion/outputs/gardens_reviewed.json` (dry-run). Utiliser `--apply` seulement après revue, avec `GARDNAIZE_ML_DATABASE_URL` configurée.

Pour les marchands, `authorized_sources.py` accepte uniquement des CSV locaux disposant d'un manifeste d'autorisation; aucun scraping n'est implémenté. Les offres normalisées au format JSON peuvent être importées avec `database/scripts/import_merchant_offers.py` (dry-run par défaut).

**Ne pas committer** les images sans droits de redistribution, les CSV commerciaux sous licence restrictive ni les données personnelles. La revue ne crée pas de masques de segmentation; ces annotations constituent un travail séparé. L'import des offres suppose une plante canonique et une source approuvée déjà présentes en base.
