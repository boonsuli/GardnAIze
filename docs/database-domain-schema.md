# PostgreSQL domain schema — MVP proposal

## Scope and status

Initial, reviewable Flyway migration: `backend/src/main/resources/db/migration/V10__gardnaize_domain_schema.sql`. It creates schema `gardnaize` and 11 tables. **Proposed structure, not a finalized botanical ontology.** No dataset import, trained model, application entity mapping or database execution is claimed by this change.

## Naming convention

- `plant_*`: botanical catalog and care traits.
- `garden_*`: garden projects, questionnaires and image references.
- `ml_*`: model versions, experiments and recommendation runs.
- `assoc_*`: explicit join/association tables; foreign keys are named after referenced entities (e.g. `plant_id`, `garden_id`, `recommendation_id`).
- `ingest_*`: import batches and auditability; `ref_*`: source metadata.

All tables are qualified by PostgreSQL schema `gardnaize`. IDs are bigint identity for catalog/reference entities, UUID for garden and run entities. The application supplies UUID values.

## Relationships

- `ref_data_source (1) -> (N) ingest_batch`
- `plant_species (1) -> (0..1) plant_care_profile`
- `garden_project (1) -> (N) garden_image`
- `garden_project (1) -> (N) ml_recommendation`
- `ml_model_version (1) -> (N) ml_recommendation` (nullable for rules-only)
- `ml_model_version (1) -> (N) ml_experiment` (optional)
- `plant_species (N) <-> (N) ref_data_source` through `assoc_plant_source`
- `ml_recommendation (N) <-> (N) plant_species` through `assoc_recommendation_plant` (rank, score, explanation).

## Notebook and pipeline boundaries

1. **Plants notebook:** sample source CSV/API, profile columns and missing values, normalize units and categorical values, deduplicate, verify source license and provenance, propose mapping to `plant_species` and `plant_care_profile`. Move validated transformations into repeatable Python ingestion scripts; record `ingest_batch` and `assoc_plant_source`.
2. **Gardens notebook:** profile garden data and labels, distinguish questionnaire inputs from image metadata, evaluate whether supervised labels exist. Store only consented, appropriate garden metadata; store photos externally and keep an `object_key` in `garden_image`.
3. **ML notebook(s):** hard horticultural constraints first; compare KNN for similarity and K-means for exploration. Train Random Forest only if reliable labeled targets exist. CNN/TensorFlow/Keras is out of the MVP baseline because external Gemini vision is the selected image-analysis path.
4. **Application:** FastAPI can load versioned scikit-learn artifacts; PostgreSQL stores model metadata, experiments, recommendation runs and ranked plant IDs. Never claim a model is trained just because its table exists.

## Review checklist

- Verify botanical fields and enum vocabularies against actual source datasets; expand only after a representative ingestion sample.
- Confirm data licensing, redistribution/commercial-use terms and attribution.
- Confirm climate/soil/sun/water measurement definitions, units and null semantics.
- Validate migrations against a fresh PostgreSQL 18 database using Flyway; run integration tests before merge.
- Check any pre-existing Flyway migration version sequence before merge; rename V10 if repository migration history requires a different version.
- Decide application schema configuration: SQL tables live in `gardnaize`, while Flyway history may remain in `public`; JPA must use explicit schema or `hibernate.default_schema` if entities map to these tables.
- Add reproducible importer with transactions, deduplication and rejection handling; no notebook should be the sole production import mechanism.
- Ensure photos, personal information and API credentials are never embedded in import source rows or model artifacts.

## Explicit exclusions

No image binary storage in PostgreSQL; no trained CNN; no model binaries in relational tables; no automatic migrations for dataset-specific unverified attributes; no user-account/retailer multi-tenancy in this MVP schema.
