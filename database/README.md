# GardnAIze — Application and horticultural data

<p align="left">
  <img alt="Database: PostgreSQL 18" src="https://img.shields.io/badge/Database-PostgreSQL%2018-4169E1" />
  <img alt="Migrations: Flyway" src="https://img.shields.io/badge/Migrations-Flyway-CC0200" />
  <img alt="Schema: Horticulture" src="https://img.shields.io/badge/Schema-Horticulture-228B22" />
  <img alt="Catalog: Provenance" src="https://img.shields.io/badge/Catalog-Provenance-7952B3" />
</p>

[Wiki de démarrage local](https://github.com/boonsuli/GardnAIze/wiki)

GardnAIze separates application persistence from horticultural and machine-learning data.

| Database | Purpose |
| --- | --- |
| `gardnaize` | Gardens, photos, questionnaire answers, consent, asynchronous workflow and recommendations; managed by GDAI-BACK |
| `gardnaize_ml` | `horticulture` schema: plant taxonomy, source provenance, catalog attributes and ML datasets |

The plant catalog is intended to supply climate, exposure, soil, water and plant-growth attributes to GDAI-PLANT's Random Forest workflow. Potential commercial contexts include plant retailers and e-commerce catalogs such as Truffaut, Leroy Merlin, botanic and Willemse; these examples do not imply partnership, permission or data licensing. Research-stage scraping must be reviewed separately for commercial use, including database rights, images, descriptions, source terms and provenance. Taxonomic sources alone do not necessarily contain horticultural suitability information. Catalog completeness and model-ready labels must be verified; migrations alone do not populate a usable catalog.

## Initialize ML schema

From the repository root:

```bash
docker compose -f compose.yaml -f compose.ml.yaml --profile ml run --rm flyway-ml
```

## Verify

```bash
docker compose -f compose.yaml -f compose.ml.yaml exec -T postgres psql -U gardnaize -d gardnaize_ml -c "SELECT count(*) FROM horticulture.plant;"
```

Applied Flyway migrations are immutable; new schema changes use new migration files. Keep dataset licenses and source provenance with imported records. Application and ML databases do not use cross-database foreign keys.

**E2E demonstration objective:** 15 December 2026.
