# Realistic garden scenario proposals (GDAI-PLANT)

This is an **offline dataset-preparation tool**, not a production recommendation endpoint.

- Generate up to 50 garden-zone proposals with Gemini using `GEMINI_API_KEY` and a configured model.
- Validate enumerated fields, ranges, contradictions, provenance and exact duplicate feature profiles.
- Emit `ACCEPTED`, `REVIEW_REQUIRED`, `REJECTED` with reasons.
- Never write to PostgreSQL, automatically label garden–plant compatibility, or treat synthetic profiles as observations.
- `ACCEPTED` means automated checks passed, **not horticultural expert validation**.
- Rare climate combinations, subtle seasonal conflicts and near-duplicates still require additional review.
- The 40-plant catalog remains unreviewed; do not train on unvalidated associations.

Run from `gdai-plant/`:

```bash
python -m unittest discover -s tests -p 'test_realistic_scenarios.py'
pip install google-genai  # optional, only for live generation
export GEMINI_API_KEY=...  # never commit secrets
export GDAI_PLANT_GEMINI_MODEL=...  # use an available model
python -m matching.generate_garden_scenarios --count 50 --out /tmp/garden-reviews.json
# Offline test / replay without API charges:
python -m matching.generate_garden_scenarios --count 50 --input-json /tmp/gemini.json --out /tmp/garden-reviews.json
```

Next steps: add regional plausibility reference data, near-duplicate detection, explicit human review, dataset versioning, then separately evaluate garden–plant pairs. The 50 scenarios x 40 plants = 2,000 *potential* pairs, not 2,000 expert-labelled examples.
