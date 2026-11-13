"""Transactional reviewed-garden manifest importer; dry-run by default."""
import argparse
import json
import os
from pathlib import Path

def import_records(conn, records):
    with conn.transaction():
        with conn.cursor() as cur:
            for r in records:
                if r.get("review_status") not in ("PENDING","ACCEPTED","REJECTED","UNCERTAIN"):
                    raise ValueError("Invalid review status")
                if not all(r.get(k) for k in ("source_key","external_id","garden_group_key","image_path")):
                    raise ValueError("Missing required garden fields")
                split=r.get("dataset_split") or None
                if split and (r["review_status"]!="ACCEPTED" or split not in ("TRAIN","VAL","TEST")):
                    raise ValueError("Invalid split")
                cur.execute("""
                  INSERT INTO horticulture.garden_image_candidate
                  (source_key,external_id,image_uri,garden_group_key,license_name,redistribution_allowed,
                   climate_zone,soil_type,exposure,review_status,review_reason,reviewed_at,dataset_split)
                  VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                          CASE WHEN %s='PENDING' THEN NULL ELSE now() END,%s)
                  ON CONFLICT (source_key,external_id) DO UPDATE SET
                   review_status=EXCLUDED.review_status,review_reason=EXCLUDED.review_reason,
                   reviewed_at=EXCLUDED.reviewed_at,dataset_split=EXCLUDED.dataset_split
                """,(r["source_key"],r["external_id"],r["image_path"],r["garden_group_key"],
                     r.get("license_name"),str(r.get("redistribution_allowed","")).lower() in ("true","1","yes"),
                     r.get("climate_zone"),r.get("soil_type"),r.get("exposure"),r["review_status"],
                     r.get("review_reason"),r["review_status"],split))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("json_file",type=Path)
    p.add_argument("--apply",action="store_true")
    args=p.parse_args()
    rows=json.loads(args.json_file.read_text(encoding="utf-8"))
    print(f"{len(rows)} garden records; dry-run={not args.apply}")
    if not args.apply: return
    dsn=os.environ.get("GARDNAIZE_ML_DATABASE_URL")
    if not dsn: raise SystemExit("GARDNAIZE_ML_DATABASE_URL required")
    import psycopg
    with psycopg.connect(dsn) as conn: import_records(conn,rows)

if __name__=="__main__": main()
