"""Import GBIF JSON or approved WCVP/Tela CSV into ML staging. Dry-run default."""
import argparse,csv,json,os
from pathlib import Path

def records(path,source,version):
    if path.suffix.lower()==".json":
        if source!="GBIF":
            raise ValueError("JSON currently supported only for GBIF")
        data=json.loads(path.read_text(encoding="utf-8"))
        for row in data:
            if row.get("error") or not row.get("gbif_usage_key") or not row.get("input_name"):
                continue
            yield (source,str(row["gbif_usage_key"]),row["input_name"],
                   row.get("canonical_name"),row["source_url"],version,json.dumps(row))
    else:
        if source not in ("WCVP","TELA_BOTANICA","MERCHANT_AUTHORIZED"):
            raise ValueError("CSV source must be WCVP, TELA_BOTANICA or MERCHANT_AUTHORIZED")
        with path.open(encoding="utf-8-sig",newline="") as f:
            for row in csv.DictReader(f):
                if not all(row.get(k) for k in ("external_id","scientific_name","source_url")):
                    continue
                yield (source,row["external_id"],row["scientific_name"],
                       row.get("canonical_name"),row["source_url"],version,json.dumps(row,ensure_ascii=False))
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--source",choices=["GBIF","WCVP","TELA_BOTANICA","MERCHANT_AUTHORIZED"],required=True)
    p.add_argument("--source-version",required=True)
    p.add_argument("--permission-reviewed",action="store_true",
                   help="Operator confirms licence and commercial reuse review")
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    if not a.permission_reviewed:
        raise SystemExit("Review and document source licence before import; pass --permission-reviewed")
    rows=list(records(a.input,a.source,a.source_version))
    print(f"source={a.source} records={len(rows)} apply={a.apply}")
    if not a.apply:
        return
    dsn=os.getenv("GARDNAIZE_ML_DATABASE_URL")
    if not dsn:
        raise SystemExit("GARDNAIZE_ML_DATABASE_URL required")
    import psycopg
    with psycopg.connect(dsn.replace('postgresql+psycopg://','postgresql://',1)) as conn:
        with conn.cursor() as cur:
            for row in rows:
                cur.execute("""INSERT INTO horticulture.ml_taxon_source_staging
                  (source_key,external_id,scientific_name,canonical_name,source_url,source_version,payload)
                  VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)
                  ON CONFLICT (source_key,external_id) DO UPDATE SET
                    scientific_name=EXCLUDED.scientific_name,
                    canonical_name=EXCLUDED.canonical_name,
                    source_url=EXCLUDED.source_url,
                    source_version=EXCLUDED.source_version,
                    payload=EXCLUDED.payload,
                    retrieved_at=now(),review_status='PENDING'""",row)
        conn.commit()
    print("Staged for review; no canonical horticultural attributes promoted")
if __name__=="__main__":
    main()
