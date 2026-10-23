# GardnAIze PostgreSQL — horticulture schema

PostgreSQL 18 SQL scripts. All identifiers and controlled vocabularies use English.

## Execution order

1. `001_create_horticulture_reference_and_plants.sql`
2. `002_create_gardens_and_ml_assessments.sql`
3. `003_seed_horticulture_lookups.sql`

Run with `psql -v ON_ERROR_STOP=1 -h localhost -U gardnaize -d gardnaize -f database/scripts/001_create_horticulture_reference_and_plants.sql` (repeat for 002 and 003). Docker Compose currently keeps PostgreSQL internal; alternatively run `docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U gardnaize -d gardnaize < database/scripts/001_create_horticulture_reference_and_plants.sql`.

**Important:** these scripts are a proposed, standalone schema and are **not** automatically applied by Flyway or Docker Compose. The existing Spring Boot application uses Flyway and JPA `ddl-auto: validate`. Before production integration, review existing Flyway migrations and move/adapt these DDL statements to properly versioned migrations, then map Java entities. Do not run competing DDL paths in the same environment.

## Terminology

- `plant`: canonical botanical taxon/cultivar record; `plant_source_record`: provider-specific original payload.
- `plant_soil_type`, `plant_sun_exposure`, `plant_use_assignment`, `plant_color_assignment`: many-to-many relationships; suitability and color context live on the association where applicable.
- `garden`: physical site and preferences; `garden_soil_type`, `garden_sun_exposure`, `garden_plant_use_preference`: site conditions and user goals.
- `garden_plant_assessment`: independently assessed garden–plant relevance label, **not** a recommendation.
- `garden_plant_recommendation`: algorithm output linked to a `recommendation_run`.
- `plant_attribute_evidence`: raw observed, expert-reviewed or predicted attribute evidence. Predicted values must never silently overwrite verified values in `plant`.

## Machine learning

Features: categorical type, exposure, soil, water, pruning, fertilizer, maintenance, evergreen; numeric size, temperature tolerance, soil pH, spacing; plant uses/colors/flowering season; garden site conditions and preferences. Labels: known plant care needs for supervised training; independent `garden_plant_assessment` relevance for ranking. `ml_experiment` records algorithm, dataset/code version, evaluation and metrics.

Use `quality_status='VALIDATED'` and explicit evidence provenance for ML exports. Missing values are nullable; do not turn unknown into negative. Split by garden for garden–plant assessments and group botanical synonyms/cultivars when appropriate to avoid leakage. Avoid exposing optional precise coordinates in shared datasets.

## Limitations and follow-ups

This is a **schema proposal**, not a validated botanical dataset. Real ingestion must reconcile botanical synonyms, units, multiple source disagreements and provider licensing. The `normalized_scientific_name` unique constraint is a provisional canonicalization strategy. App-level storage of uploaded images currently differs; `garden_photo.storage_key` is an intended future storage reference. Add migrations, automated SQL integration tests, retention/privacy rules and a curated taxonomic identity strategy before enabling production writes.
