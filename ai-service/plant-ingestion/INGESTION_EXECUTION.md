# PR #30 ingestion execution

## Garden photos
- Already reviewed images in `horticulture.garden_image_candidate` are the ML dataset, not application photos.
- `gemini_garden_batch.py` is read-only by default. `--apply` sends each eligible image to the Gemini API, charges API credits, and stores a JSON observation in `ml_garden_features` with `reviewed=false`.
- Set `GEMINI_API_KEY`, `GARDNAIZE_ML_DATABASE_URL`, and optionally `GEMINI_VISION_MODEL`. Check model availability in your own account.
- Image paths must resolve inside `ai-service/plant-ingestion/inputs/images`. No photos are copied to the application database.
- Commands from repository root:
```bash
python ai-service/plant-ingestion/gemini_garden_batch.py --limit 31
python ai-service/plant-ingestion/gemini_garden_batch.py --limit 2 --apply
```
- After verifying results and costs, run `--limit 31 --apply`. Inspect and review outputs before setting `reviewed=true`; NULL visual observations cannot be used in the six-boolean K-Means baseline.
- API failures are logged and do not create validated training features.

## Botanical sources
- GBIF: documented taxonomic match API; `gbif_taxonomy.py` reads an input CSV with `scientific_name` and saves API response/provenance. It does not infer exposure, soil, or watering needs.
- POWO: use official WCVP versioned downloadable releases after licence review; **no automated POWO HTML scraping**.
- Tela Botanica: approved official export/API integration pending verification; **no unverified API endpoints**.
- Merchants: use permissioned CSV feeds or documented partner APIs; match by scientific name **plus cultivar**. Common-name-only and ambiguous synonym matches require review. No merchant crawling is enabled.
- `questionnaire_plant_mapping.py` defines question-to-field mapping; missing attributes remain missing.

## PostgreSQL
Run Flyway ML migrations V6-V8. Source staging is deliberately separate from `horticulture.plant` to prevent automatic promotion of unverified names or care characteristics.
```bash
python ai-service/plant-ingestion/gbif_taxonomy.py --input path/to/plants.csv
python ai-service/plant-ingestion/gbif_taxonomy.py --input path/to/plants.csv --apply
python database/scripts/import_taxon_staging.py --source GBIF --source-version 2026-11-16 --input ai-service/plant-ingestion/outputs/gbif_matches.json --permission-reviewed
python database/scripts/import_taxon_staging.py --source GBIF --source-version 2026-11-16 --input ai-service/plant-ingestion/outputs/gbif_matches.json --permission-reviewed --apply
```
WCVP, Tela or licensed merchant CSV must have `external_id,scientific_name,source_url`; optionally `canonical_name`. Explicit `--permission-reviewed` is an operator assertion, not automated rights validation. Do not commit unlicensed data.

## Outstanding
- Real botanical/merchant feeds and licence verification
- Merge taxonomic synonyms using authority identifiers and review, not fuzzy auto-merge
- Promote reviewed records to canonical plant tables with field-level evidence
- Gemini batch integration tests with mocked HTTP and database, error retry/backoff
- KNN/K-Means and Random Forest evaluation, end-to-end CI, security/privacy review
