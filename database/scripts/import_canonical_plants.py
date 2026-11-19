"""Idempotent, transactional import of reviewed licensed canonical plant JSON.

Run after Flyway V1-V4. Default is dry-run. No database writes unless --apply.
Never sets ready_for_matching or quality_status=VALIDATED automatically.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

def validate_record(plant):
    if not plant.get("scientific_name"):
        raise ValueError("scientific_name is required")
    if not plant.get("sources"):
        raise ValueError("at least one source is required")
    return plant

def import_plants(connection, plants):
    from psycopg import sql
    with connection.transaction():
        for p in plants:
            validate_record(p)
            name = " ".join(p["scientific_name"].casefold().split())
            cultivar = (p.get("cultivar") or "").casefold().strip()
            key = name + (" | " + cultivar if cultivar else "")
            with connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO horticulture.plant
                        (scientific_name, normalized_scientific_name, common_name,
                         cultivar, is_outdoor, european_climate_compatible,
                         quality_status, ready_for_matching)
                    VALUES (%s,%s,%s,%s,%s,%s,'PENDING',false)
                    ON CONFLICT (normalized_scientific_name)
                    DO UPDATE SET
                        common_name = COALESCE(horticulture.plant.common_name, EXCLUDED.common_name),
                        updated_at = now()
                    RETURNING plant_id
                """, (p["scientific_name"], key, p.get("common_name"),
                      p.get("cultivar"), str(p.get("outdoor")).lower() in ("true","1","yes"),
                      str(p.get("europe_compatible")).lower() in ("true","1","yes")))
                plant_id = cur.fetchone()[0]
                for source in p["sources"]:
                    cur.execute("""
                        SELECT data_source_id FROM horticulture.data_source
                        WHERE source_name = %s AND commercial_reuse_allowed IS TRUE
                    """, (source,))
                    found = cur.fetchone()
                    if not found:
                        raise ValueError(f"Source not approved in database: {source}")
                    cur.execute("""
                        INSERT INTO horticulture.plant_attribute_evidence
                            (plant_id, attribute_name, data_source_id, value_as_reported, evidence_type)
                        VALUES (%s,'ingested_record',%s,%s::jsonb,'OBSERVED')
                    """, (plant_id, found[0], json.dumps(p, ensure_ascii=False)))
                for field in p.get("missing_required") or []:
                    cur.execute("""
                        INSERT INTO horticulture.plant_ingestion_review
                            (plant_id,canonical_key,issue_type,details)
                        VALUES (%s,%s,'MISSING',%s::jsonb)
                    """, (plant_id,key,json.dumps({"field":field})))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    plants = json.loads(args.json_file.read_text(encoding="utf-8"))
    for plant in plants:
        validate_record(plant)
    print(f"Validated input structure: {len(plants)} plants")
    if not args.apply:
        print("DRY RUN: no PostgreSQL changes. Pass --apply to insert.")
        return
    dsn = os.environ.get("GARDNAIZE_ML_DATABASE_URL")
    if not dsn or not dsn.startswith(("postgresql://","postgres://")):
        raise SystemExit("Set GARDNAIZE_ML_DATABASE_URL to a psycopg PostgreSQL DSN")
    import psycopg
    with psycopg.connect(dsn) as connection:
        import_plants(connection, plants)
    print("Transaction committed; records remain PENDING")

if __name__ == "__main__":
    main()
