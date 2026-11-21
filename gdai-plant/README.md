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
