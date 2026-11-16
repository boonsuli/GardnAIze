# ML data boundaries and lineage (PR #30)

## Current truth
The merchant/scientific notebooks accept authorized local CSV files; they do not
download GBIF, POWO or merchant catalogs. Questionnaire-related plant fields
exist in horticulture.plant but have not been verified as populated.
The existing KNN/K-Means research notebooks do not read production PostgreSQL.
The new postgres_ml.py provides **K-Means and optional supervised KNN integration baselines**, not a finished image classifier or pre-trained models. It needs manually reviewed visual features.

## Isolation
- gardnaize.app_schema: user photo, answers, consent and live recommendations.
- gardnaize_ml.horticulture: curated source datasets, feature provenance,
  immutable dataset versions, split membership and experiment results.
- Do not query/copy application photos directly into ML. Require separate,
  recorded, revocable training consent, minimization, admission review and
  a deliberate transfer process. No cross-database foreign keys.
- Dataset image paths are references; V6 does not store image bytes.
- Frozen dataset rows must not be edited. Database permissions or triggers
  should enforce immutability before production use.

## Run
Apply Flyway ML V6 from repo root:
```bash
docker compose -f compose.yaml -f compose.ml.yaml --profile ml run --rm flyway-ml
```
Snapshot reviewed accepted gardens (read-only preview first):
```bash
python database/scripts/snapshot_garden_dataset.py --version 2026-11-16
python database/scripts/snapshot_garden_dataset.py --version 2026-11-16 --apply
```
Add manually checked garden feature JSON in ml_garden_features. Required boolean
keys: lawn, terrace, pathway, trees, shrubs, fence. A NULL/missing value is
not automatically interpreted as false. Mark reviewed=true only after checking
the image and analysis. Do not use Gemini predictions as verified ground truth.
```bash
python ai-service/plant-ingestion/postgres_ml.py --dataset-id 1 --clusters 3
python ai-service/plant-ingestion/postgres_ml.py --dataset-id 1 --clusters 3 --apply
# KNN requires at least two independent HUMAN/EXPERT-labelled TRAIN records
# spanning at least two classes in horticulture.ml_garden_label:
python ai-service/plant-ingestion/postgres_ml.py --dataset-id 1 --label-type garden_style
```
Replace dataset-id with the ID printed by the snapshot script. K-Means fits
on TRAIN only; VAL/TEST receive assignments but are not used for fitting.
This is a six-boolean baseline, not an image embedding model.

## Next work
- Authorized botanical provider imports and evidence-based questionnaire fields.
- Extract visual features from accepted images (Gemini Vision or local model)
  with model provenance and human review.
- Populate expert-labelled classes and add split-safe KNN evaluation metrics.
- Snapshot plant datasets, persist ML experiment metrics and model artifacts,
  enforce snapshot immutability, add integration tests and CI.
- Image SHA256 must be calculated from image bytes; current snapshot fallback
  hashes metadata only and must not be mistaken for image integrity.
