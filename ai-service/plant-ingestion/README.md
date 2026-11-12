# Plant ingestion — new isolated notebooks

Existing `notebooks/` and `ai-service/notebooks/` are untouched.

## Security and rights
No notebook scrapes a merchant website. The three notebooks read **local CSV exports only**, gated by an explicit source manifest. A robots.txt allow rule is not a reuse licence. Verify licence, attribution, redistribution, commercial usage, and image rights separately. Do not commit unlicensed datasets.

## Workflow
1. Obtain an authorized CSV export from a scientific provider, a dataset provider, or a merchant partner.
2. Map its columns to the canonical template (see `sample_input.csv`).
3. Edit the notebook's manifest and `input_csv` path, with verified permissions.
4. Run each source notebook to produce normalized records.
5. Run `004_merge_quality.ipynb` to merge on normalized scientific name + cultivar, audit conflicts, and export CSV/JSON.
6. Human-review `READY_FOR_REVIEW` plants before matching. No database writes are performed.

A canonical taxon key is a provisional deduplication key; accepted names, synonyms and cultivars require expert or taxonomy-authority validation. Do not automatically merge taxonomic synonyms. Source-level evidence and field conflicts must be preserved in production.

## ML
K-Means and KNN already exist as research in `ai-service/notebooks/`. Do not train models independently for each source. First combine licensed, sufficiently complete records; train and validate common feature pipelines with reliable supervised labels. Do not infer horticultural facts from clusters.

## Database
The existing `database/migrations/ml/V1__create_horticulture_reference_and_plants.sql` defines canonical plants, source records and field evidence. Import integration must be built and tested against that schema before any database mutation.

## Important
`sample_input.csv` is an empty header-only template, not botanical evidence. All outputs depend on authorized user-provided exports.

## Validation before merging PR #30
1. `python -m unittest discover -s ai-service/plant-ingestion -p 'test_*.py'` from the repository root (or run from the ingestion folder).
2. Run `python scripts/check_indentation.py` and the GitHub CI workflows.
3. Run Flyway ML using the command in `database/README.md`, then check that V4 succeeded in `horticulture.flyway_schema_history`.
4. Register each approved data source in `horticulture.data_source` with reviewed commercial permissions, using SQL parameters / audited admin tooling. Do not automatically approve unknown sources.
5. Dry-run: `python database/scripts/import_canonical_plants.py ai-service/plant-ingestion/outputs/plants.json`.
6. After review and using a psycopg DSN (not SQLAlchemy URL), use `--apply` on an isolated test database; verify source evidence and PENDING status. This importer is a **prototype**: repeat runs currently duplicate evidence/review rows; do not schedule repeated production imports.
7. Verify ML research notebooks against the consolidated dataset. They currently use synthetic-demo files and are **not yet connected** to the new exports. No KNN/K-Means retraining is claimed.
8. Confirm botanical source licences, cultivar identity, conflicts, climate suitability and labels before enabling Random Forest matching.

**Not yet merge-ready:** complete database integration tests, repeated-import idempotency, robust field-level evidence, ML data adapter and end-to-end CI.

## PostgreSQL namespace convention

Application domain: database `gardnaize`, schema `app_schema` after backend Flyway V11. Research ingestion: separate database `gardnaize_ml`, schema `horticulture`. The notebooks must not write directly to `app_schema`; publish validated, mapped exports only. Existing JPA `public` mappings are not modified by the schema rename.
