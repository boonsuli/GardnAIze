"""Import approved plant CSV into ML candidate catalogue (dry-run by default).

CSV columns: source_key,external_id,scientific_name,source_url,license_id,
commercial_reuse_allowed; optional cultivar,common_name_fr,common_name_en,
outdoor_confirmed,temperate_confirmed,growth_form,exposure,soil_texture,
water_requirement,hardiness_min_c,height_cm,spread_cm,original_image_url,
image_license_id,image_attribution,image_rights_reviewed.
No automatic web scraping or image downloads. Review before promoting candidates.
"""
import argparse, csv, json, os, re, unicodedata
from pathlib import Path

REQUIRED=("source_key","external_id","scientific_name","source_url","license_id","commercial_reuse_allowed")
FIELDS=("common_name_fr","common_name_en","growth_form","exposure","soil_texture","water_requirement")
BOOL=("outdoor_confirmed","temperate_confirmed")
NUM=("hardiness_min_c","height_cm","spread_cm")

def parse_bool(v):
    if v is None or not str(v).strip(): return None
    s=str(v).strip().lower()
    if s in ("true","yes","1"): return True
    if s in ("false","no","0"): return False
    raise ValueError("Invalid boolean: "+s)

def normalized(s):
    return " ".join(unicodedata.normalize("NFKC",str(s or "")).casefold().split())

def load(path):
    with path.open(encoding="utf-8-sig",newline="") as fh:
        reader=csv.DictReader(fh)
        if not set(REQUIRED).issubset(reader.fieldnames or []):
            raise ValueError("Missing CSV columns: "+str(set(REQUIRED)-set(reader.fieldnames or [])))
        rows=[]
        for row in reader:
            if any(not (row.get(k) or "").strip() for k in REQUIRED):
                raise ValueError("Missing mandatory value")
            if parse_bool(row["commercial_reuse_allowed"]) is not True:
                raise PermissionError("Source not approved for commercial reuse: "+row["source_key"])
            key=normalized(row["scientific_name"])+" | "+normalized(row.get("cultivar"))
            if not normalized(row["scientific_name"]):
                raise ValueError("Empty scientific name")
            row["_key"]=key
            for field in BOOL: row[field]=parse_bool(row.get(field))
            for field in NUM: row[field]=float(row[field]) if row.get(field) else None
            rows.append(row)
    return rows

def import_rows(conn,rows):
    with conn.transaction():
        with conn.cursor() as cur:
            for r in rows:
                cur.execute("""INSERT INTO horticulture.ml_plant_catalog
                    (scientific_name,cultivar,canonical_key,common_name_fr,common_name_en,
                     growth_form,outdoor_confirmed,temperate_confirmed,hardiness_min_c,
                     height_cm,spread_cm,exposure,soil_texture,water_requirement)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT(canonical_key) DO UPDATE SET updated_at=now()
                    RETURNING plant_id""",
                    (r["scientific_name"].strip(),(r.get("cultivar") or "").strip(),r["_key"],
                     *[r.get(k) or None for k in FIELDS[:3]],r["outdoor_confirmed"],
                     r["temperate_confirmed"],*[r[k] for k in NUM],
                     *[r.get(k) or None for k in FIELDS[3:]]))
                plant_id=cur.fetchone()[0]
                cur.execute("""INSERT INTO horticulture.ml_plant_source_record
                    (source_key,external_id,plant_id,source_url,source_version,license_id,
                     commercial_reuse_allowed,payload)
                    VALUES (%s,%s,%s,%s,%s,%s,true,%s::jsonb)
                    ON CONFLICT(source_key,external_id) DO UPDATE SET
                    plant_id=EXCLUDED.plant_id,source_url=EXCLUDED.source_url,
                    source_version=EXCLUDED.source_version,license_id=EXCLUDED.license_id,
                    payload=EXCLUDED.payload,retrieved_at=now()""",
                    (r["source_key"],r["external_id"],plant_id,r["source_url"],
                     r.get("source_version") or None,r["license_id"],
                     json.dumps({k:v for k,v in r.items() if not k.startswith("_")},ensure_ascii=False)))
                for field in (*FIELDS,*BOOL,*NUM):
                    value=r.get(field)
                    if value is None or value=="": continue
                    cur.execute("""INSERT INTO horticulture.ml_plant_attribute_evidence
                        (plant_id,source_key,external_id,attribute_name,value_reported)
                        VALUES (%s,%s,%s,%s,%s::jsonb)
                        ON CONFLICT(plant_id,source_key,external_id,attribute_name)
                        DO UPDATE SET value_reported=EXCLUDED.value_reported,reviewed=false""",
                        (plant_id,r["source_key"],r["external_id"],field,json.dumps(value)))
                url=(r.get("original_image_url") or "").strip()
                if url:
                    license_id=(r.get("image_license_id") or "").strip()
                    if not license_id: raise ValueError("Image license missing for "+r["scientific_name"])
                    cur.execute("""INSERT INTO horticulture.ml_plant_image
                        (plant_id,source_key,external_id,original_url,license_id,attribution,rights_reviewed)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT(plant_id,original_url) DO UPDATE SET
                        attribution=EXCLUDED.attribution,license_id=EXCLUDED.license_id""",
                        (plant_id,r["source_key"],r["external_id"],url,license_id,
                         r.get("image_attribution") or None,
                         parse_bool(r.get("image_rights_reviewed")) is True))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--csv",type=Path,required=True)
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    rows=load(a.csv)
    if not rows:
        raise SystemExit("No plant rows found: CSV contains only headers. Nothing imported.")
    print(f"records={len(rows)} unique_canonical_keys={len(set(r['_key'] for r in rows))} apply={a.apply}")
    if not a.apply: return
    import psycopg
    dsn=os.environ["GARDNAIZE_ML_DATABASE_URL"].replace("postgresql+psycopg://","postgresql://",1)
    with psycopg.connect(dsn) as conn: import_rows(conn,rows)
    print("Committed; candidates remain PENDING, images are metadata-only")
if __name__=="__main__": main()
