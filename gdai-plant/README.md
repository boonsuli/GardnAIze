# GDAI-PLANT V1 — controlled botanical import

This patch is intended to be copied into the **GardnAIze monorepo** on `feature/gdai-plant-v1`. It adds `gdai-plant/ingestion/import_plants.py` and tests. No migrations or Docker services are changed.

## Safety and limitations

- Default is **dry run**; PostgreSQL unchanged.
- The existing six-plant prototype JSON is a **candidate list only**. Its care properties are **not imported** or claimed verified.
- `--online` calls the public GBIF species match API to validate botanical identity. GBIF does **not** establish local nursery stock or horticultural suitability.
- Only `EXACT` + `SPECIES` + `ACCEPTED` + same canonical binomial gets a `plant_source_record` entry. Synonyms/cultivars require manual review.
- All new plants remain `PENDING`; existing plants are never overwritten. Repeated runs do not duplicate plants or source records.
- Reports can contain GBIF errors. Review before `--apply`. Do not commit raw reports without reviewing contents.
- No live merchant scraping, automatic expert labels, or trained Random Forest in this patch.

## Setup and dry run

From `GardnAIze/`:

```bash
mkdir -p gdai-plant/data
cp ../gdai-plant-v1/data/plants.json gdai-plant/data/plants-pilot.json
python3 gdai-plant/ingestion/import_plants.py \
  --catalog gdai-plant/data/plants-pilot.json \
  --online --report /tmp/gdai-plant-import-report.json
python3 -m unittest discover -s gdai-plant/tests -v
```

Review `/tmp/gdai-plant-import-report.json`. With no `--online`, an entirely offline dry run is possible.

## Apply to existing PostgreSQL

```bash
python3 -m venv gdai-plant/.venv
./gdai-plant/.venv/bin/python -m pip install -r gdai-plant/requirements-ingestion.txt
# Use your actual local DB credentials from .env; do not commit them.
export GDAI_PLANT_DSN='postgresql://<USER>:<PASSWORD>@127.0.0.1:5433/gardnaize_ml'
./gdai-plant/.venv/bin/python gdai-plant/ingestion/import_plants.py \
  --catalog gdai-plant/data/plants-pilot.json \
  --online --report /tmp/gdai-plant-import-report.json --apply
unset GDAI_PLANT_DSN
```

The user should inspect the report **before** applying. Avoid putting real passwords in shell history; consider a `.pgpass` file with mode 0600 or `PGSERVICE` configuration instead of embedding credentials in the URL.

## Verify

```sql
SELECT quality_status, count(*) FROM horticulture.plant GROUP BY quality_status;
SELECT count(*) FROM horticulture.plant_source_record;
```

## Next implementation increments

1. Audit horticultural attribute completeness and provenance; source licensing and permission review.
2. Approved source-specific import adapters (licensed exports / APIs) with evidence per attribute.
3. Garden profile adapter for Gemini Vision JSON + questionnaire, without inferring unknown values.
4. Candidate pair generator with rule-derived labels kept distinct from independent expert labels.
5. Random Forest training with group-safe train/validation/test splits, reproducible metrics, and fallback rules engine.


# GDAI-PLANT next increment (copy files into `GardnAIze/gdai-plant/`)

This increment reuses the existing `horticulture` PostgreSQL schema and does **not** scrape merchants or download copyrighted datasets. The merchant/scientific notebooks from `feature/plant-multisource-ingestion` accept authorized local CSVs; review and integrate them separately rather than duplicating their ingestion logic.

- `enrichment/import_evidence.py`: evidence-only, auditable import from a human-reviewed JSON manifest; `--apply` inserts provenance and evidence, **never** promotes plant status or overwrites canonical plant traits.
- `matching/build_pairs.py`: read-only diagnostic `RULE_DERIVED` garden–plant pairs. It does **not** write assessments; review before admission to ML labels. Default requires `VALIDATED` plants; `--include-pending` is for diagnostics only.
- `training/train_rf.py`: only trains on `EXPERT` labels, `CURATED` gardens and `VALIDATED` plants. Requires >=10 distinct gardens and >=2 relevance classes in train and test; grouped split by garden. No labels = no model, by design.

## Run from repo root

```bash
python -m unittest discover -s gdai-plant/tests -p 'test_pipeline.py' -v
gdai-plant/.venv/bin/python -m pip install -r gdai-plant/requirements-enrichment.txt
# Use your existing GDAI_PLANT_DSN / PGPASSWORD environment variables
# Review a manifest populated with source-specific, legally reusable facts before --apply
gdai-plant/.venv/bin/python gdai-plant/enrichment/import_evidence.py --manifest gdai-plant/examples/evidence-template.json
gdai-plant/.venv/bin/python gdai-plant/matching/build_pairs.py --out /tmp/gdai-pairs.json --include-pending
# This will intentionally refuse training until expert-labelled examples exist:
gdai-plant/.venv/bin/python gdai-plant/training/train_rf.py --out /tmp/gdai-rf.joblib
```

Do not fill `evidence-template.json` with invented facts. For each fact supply `scientific_name`, `source_name` (exact `horticulture.data_source.source_name`), `source_url` (specific source page), `attribute_name`, `value`, `evidence_type` (`OBSERVED` or `EXPERT_REVIEWED`). Source URLs and data reuse permissions must be checked before admission. An evidence record is not automatically a validated botanical trait.

Future: add reviewed feature promotion; normalized sun/soil/use tables; merchant CSV adapters from the existing branch; curated garden–plant assessment admission; snapshot versioning; test integration with real PostgreSQL; Docker/FastAPI integration.
