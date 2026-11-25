# GDAI-PLANT V1 — batch importer and API contract

Extract this archive INSIDE `GardnAIze/gdai-plant/`.

## Batch importer

```bash
PYTHONPATH=gdai-plant/ingestion gdai-plant/.venv/bin/python -m unittest discover -s gdai-plant/tests -v

gdai-plant/.venv/bin/python gdai-plant/ingestion/import_batch.py \
  --catalog gdai-plant/data/plants-pilot.json --batch-size 30 \
  --report /tmp/gdai-batch.ndjson
```

Review report before running `--online`; GBIF is a remote API. Review again before `--apply`.
`--apply` commits one batch at a time, not the whole catalog; reruns are idempotent
because the existing importer uses ON CONFLICT. Partial reports and partial DB
progress are possible after interruptions.

## API contract

```bash
gdai-plant/.venv/bin/python -m pip install -r gdai-plant/requirements-api.txt
PYTHONPATH=gdai-plant gdai-plant/.venv/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 8002
```

POST /v1/recommendations sample:

```json
{"request_id":"demo-001","garden":{"sun_exposure":"PARTIAL_SHADE","water_availability":"LOW","evergreen_preferred":true},"limit":5}
```

The endpoint intentionally returns INSUFFICIENT_DATA and zero recommendations
until an evidence-based, validated scorer is implemented. It is a contract stub,
not a completed recommendation engine. GDAI-BACK should treat INSUFFICIENT_DATA
as a non-successful recommendation outcome and avoid displaying invented plants.
