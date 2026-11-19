# GardnAIze — Application and horticultural data

<p align="left">
  <img alt="Database: PostgreSQL" src="https://img.shields.io/badge/Database-PostgreSQL-4169E1" />
  <img alt="Migrations: Flyway" src="https://img.shields.io/badge/Migrations-Flyway-CC0200" />
  <img alt="Schema: Horticulture" src="https://img.shields.io/badge/Schema-Horticulture-228B22" />
  <img alt="Catalog: Provenance" src="https://img.shields.io/badge/Catalog-Provenance-7952B3" />
</p>

GardnAIze separates application persistence from horticultural and machine-learning data.

| Database | Purpose |
| --- | --- |
| `gardnaize` | Gardens, photos, questionnaire answers, consent, asynchronous workflow and recommendations; managed by GDAI-BACK |
| `gardnaize_ml` | `horticulture` schema: plant taxonomy, source provenance, catalog attributes and ML datasets |

The plant catalog is intended to supply climate, exposure, soil, water and plant-growth attributes to GDAI-PLANT's Random Forest workflow. Potential commercial contexts include plant retailers and e-commerce catalogs such as Truffaut, Leroy Merlin, botanic and Willemse; these examples do not imply partnership, permission or data licensing. Research-stage scraping must be reviewed separately for commercial use, including database rights, images, descriptions, source terms and provenance. Taxonomic sources alone do not necessarily contain horticultural suitability information. Catalog completeness and model-ready labels must be verified; migrations alone do not populate a usable catalog.

## Initialize and migrate

From the repository root:
```bash
docker compose -f compose.yaml -f compose.ml.yaml --profile ml run --rm flyway-ml
```
The one-shot `postgres-ml-init` uses `psql` to create `gardnaize_ml` only if absent, then Flyway applies the pending migrations to `horticulture`. Database creation is not a Flyway migration (PostgreSQL CREATE DATABASE cannot execute inside a transaction and Flyway needs to connect to an existing database). No database or volume is deleted. Do not execute the retired manual scripts.

## Verify
```bash
docker compose -f compose.yaml -f compose.ml.yaml exec -T postgres psql -U gardnaize -d gardnaize_ml -c "SELECT version,description,success FROM horticulture.flyway_schema_history ORDER BY installed_rank;"
docker compose -f compose.yaml -f compose.ml.yaml exec -T postgres psql -U gardnaize -d gardnaize_ml -c "SELECT count(*) FROM horticulture.plant;"
```
V3 seeds lookups; it does not ingest real plants. `horticulture.plant` starts empty.

## Notebook (WSL2 / VS Code)
PostgreSQL is exposed on loopback port `5433` only with `compose.ml.yaml`. Configure a WSL environment variable, never commit credentials:
```bash
conda activate demo-env
python -m pip install -r database/requirements-notebook.txt
python -m ipykernel install --user --name demo-env --display-name "Python (GardnAIze ML)"
export GARDNAIZE_ML_DATABASE_URL='postgresql+psycopg://gardnaize:YOUR_PASSWORD@127.0.0.1:5433/gardnaize_ml'
```
Launch VS Code from that environment (`code .`) and open `notebooks/01_verify_ml_database.ipynb`. Replace YOUR_PASSWORD with the local password; URL-encode special characters. Select the `demo-env` kernel.

## Conventions
- Only `database/migrations/ml/V*__*.sql` defines the ML database structure. Applied migrations must never be edited; add a new versioned migration.
- Training samples are not canonical user projects. No duplicate user garden/photo/recommendation tables in the ML database.
- No foreign keys across PostgreSQL databases. Use APIs and explicit synchronization.
- ML Flyway CLI is independent of Spring Boot 3.5.7; never upgrade backend Flyway to 13 without compatibility testing.
- Check image tag availability and execute an integration test before merging.

**E2E demonstration objective:** 15 December 2026.
